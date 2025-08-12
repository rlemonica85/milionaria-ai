"""Módulo para coleta de dados da CAIXA usando Playwright de forma assíncrona."""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
from playwright.async_api import async_playwright, Page, Browser
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..utils.caixa_selectors import (
    CAIXA_MILIONARIA_URL,
    CSS_SELECTORS,
    extract_all_data
)
from ..utils.metrics import setup_logger

# Configura logger
logger = setup_logger(__name__)


class FetchError(Exception):
    """Exceção customizada para erros de coleta."""
    pass


class CaixaFetcher:
    """Classe para coleta de dados da +Milionária da CAIXA."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Cria diretório para logs HTML
        self.logs_dir = Path("logs/html")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"CaixaFetcher inicializado - headless: {headless}, timeout: {timeout}ms")
    
    async def __aenter__(self):
        """Context manager para inicializar o browser."""
        logger.info("Iniciando browser Playwright...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        
        # Configurações da página
        await self.page.set_viewport_size({"width": 1280, "height": 720})
        self.page.set_default_timeout(self.timeout)
        
        logger.info("Browser Playwright inicializado com sucesso")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager para fechar o browser."""
        logger.info("Fechando browser Playwright...")
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Browser Playwright fechado")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((FetchError, Exception))
    )
    async def _load_page(self) -> None:
        """Carrega a página inicial da +Milionária."""
        try:
            logger.info(f"Carregando página: {CAIXA_MILIONARIA_URL}")
            await self.page.goto(CAIXA_MILIONARIA_URL, wait_until="networkidle")
            await asyncio.sleep(2)  # Aguarda carregamento completo
            logger.info("Página carregada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar página: {e}")
            raise FetchError(f"Erro ao carregar página: {e}")
    
    def _parse_block(self, text: str) -> Dict[str, Union[int, str, None]]:
        """Extrai dados de um bloco de texto da página.
        
        Args:
            text (str): Texto da página
            
        Returns:
            Dict[str, Union[int, str, None]]: Dados extraídos
        """
        return extract_all_data(text)
    
    async def _save_snapshot(self, concurso: int, content: str) -> None:
        """Salva snapshot HTML para auditoria.
        
        Args:
            concurso (int): Número do concurso
            content (str): Conteúdo HTML da página
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{concurso}_{timestamp}.txt"
        filepath = self.logs_dir / filename
        
        logger.info(f"Salvando snapshot para concurso {concurso}: {filename}")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Concurso: {concurso}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"URL: {CAIXA_MILIONARIA_URL}\n")
                f.write("=" * 80 + "\n")
                f.write(content)
        except Exception as e:
            print(f"Aviso: Erro ao salvar snapshot para concurso {concurso}: {e}")
    
    async def _navigate(self, direction: str) -> bool:
        """Navega para próximo ou anterior concurso.
        
        Args:
            direction (str): 'next' para próximo, 'prev' para anterior
            
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        selectors_key = 'navegacao_proximo' if direction == 'next' else 'navegacao_anterior'
        selectors = CSS_SELECTORS[selectors_key]
        
        for selector in selectors:
            try:
                # Tenta encontrar e clicar no elemento
                element = await self.page.query_selector(selector)
                if element:
                    # Verifica se o elemento está visível e habilitado
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    
                    if is_visible and is_enabled:
                        await element.click()
                        await asyncio.sleep(3)  # Aguarda carregamento
                        return True
            except Exception:
                continue
        
        # Fallback: tenta encontrar por texto
        text_patterns = ['Próximo', 'Proximo', 'Next'] if direction == 'next' else ['Anterior', 'Previous', 'Prev']
        
        for pattern in text_patterns:
            try:
                element = await self.page.get_by_text(pattern).first
                if element:
                    await element.click()
                    await asyncio.sleep(3)
                    return True
            except Exception:
                continue
        
        return False
    
    async def _get_current_data(self) -> Optional[Dict[str, Union[int, str, None]]]:
        """Obtém dados do concurso atual na página.
        
        Returns:
            Optional[Dict]: Dados do concurso ou None se não encontrados
        """
        try:
            # Obtém todo o texto visível da página
            page_text = await self.page.inner_text('body')
            
            # Também obtém o HTML para snapshot
            page_html = await self.page.content()
            
            # Extrai dados usando os padrões regex
            data = self._parse_block(page_text)
            
            # Salva snapshot se conseguiu extrair concurso
            if data.get('concurso'):
                await self._save_snapshot(data['concurso'], page_html)
            
            # Valida se conseguiu extrair dados mínimos
            if data.get('concurso') and data.get('data'):
                return data
            
            return None
            
        except Exception as e:
            print(f"Erro ao extrair dados da página: {e}")
            return None
    
    async def _navigate_to_concurso(self, target_concurso: int, max_attempts: int = 50) -> bool:
        """Navega até um concurso específico.
        
        Args:
            target_concurso (int): Número do concurso alvo
            max_attempts (int): Máximo de tentativas de navegação
            
        Returns:
            bool: True se encontrou o concurso
        """
        for attempt in range(max_attempts):
            current_data = await self._get_current_data()
            
            if not current_data or not current_data.get('concurso'):
                print(f"Tentativa {attempt + 1}: Não foi possível extrair dados da página")
                await asyncio.sleep(2)
                continue
            
            current_concurso = current_data['concurso']
            
            if current_concurso == target_concurso:
                return True
            elif current_concurso < target_concurso:
                # Precisa ir para frente
                if not await self._navigate('next'):
                    print(f"Não foi possível navegar para próximo concurso")
                    break
            else:
                # Precisa ir para trás
                if not await self._navigate('prev'):
                    print(f"Não foi possível navegar para concurso anterior")
                    break
            
            await asyncio.sleep(1)
        
        return False
    
    async def fetch_range(
        self, 
        start_concurso: Optional[int] = None, 
        to_latest: bool = True
    ) -> pd.DataFrame:
        """Coleta dados de um intervalo de concursos.
        
        Args:
            start_concurso (Optional[int]): Concurso inicial (None para atual)
            to_latest (bool): Se deve coletar até o último disponível
            
        Returns:
            pd.DataFrame: DataFrame com dados coletados
        """
        await self._load_page()
        
        collected_data = []
        
        # Se especificou concurso inicial, navega até ele
        if start_concurso is not None:
            print(f"Navegando para concurso {start_concurso}...")
            if not await self._navigate_to_concurso(start_concurso):
                raise FetchError(f"Não foi possível encontrar concurso {start_concurso}")
        
        # Coleta dados do concurso atual
        current_data = await self._get_current_data()
        if current_data and current_data.get('concurso'):
            collected_data.append(current_data)
            print(f"Coletado concurso {current_data['concurso']}")
        
        # Se deve coletar até o último, continua navegando
        if to_latest:
            max_iterations = 1000  # Limite de segurança
            
            for i in range(max_iterations):
                # Tenta navegar para próximo
                if await self._navigate('next'):
                    await asyncio.sleep(2)
                    
                    # Coleta dados do novo concurso
                    next_data = await self._get_current_data()
                    
                    if next_data and next_data.get('concurso'):
                        # Verifica se não é duplicata
                        if not any(d.get('concurso') == next_data['concurso'] for d in collected_data):
                            collected_data.append(next_data)
                            print(f"Coletado concurso {next_data['concurso']}")
                        else:
                            print(f"Concurso {next_data['concurso']} já coletado, parando")
                            break
                    else:
                        print("Não foi possível extrair dados, tentando continuar...")
                        continue
                else:
                    print("Chegou ao último concurso disponível")
                    break
        
        # Converte para DataFrame
        if not collected_data:
            raise FetchError("Nenhum dado foi coletado")
        
        df = pd.DataFrame(collected_data)
        
        # Garante que tem as colunas necessárias
        required_columns = ['concurso', 'data', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 't1', 't2']
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # Ordena por concurso
        df = df.sort_values('concurso').reset_index(drop=True)
        
        # Seleciona apenas as colunas necessárias
        df = df[required_columns]
        
        print(f"Coletados {len(df)} concursos")
        return df


# Função de conveniência para uso direto
async def fetch_caixa_data(
    start_concurso: Optional[int] = None,
    to_latest: bool = True,
    headless: bool = True
) -> pd.DataFrame:
    """Função de conveniência para coletar dados da CAIXA.
    
    Args:
        start_concurso (Optional[int]): Concurso inicial
        to_latest (bool): Se deve coletar até o último
        headless (bool): Se deve executar em modo headless
        
    Returns:
        pd.DataFrame: Dados coletados
    """
    async with CaixaFetcher(headless=headless) as fetcher:
        return await fetcher.fetch_range(start_concurso, to_latest)


if __name__ == "__main__":
    # Exemplo de uso
    async def main():
        print("Testando coleta de dados da CAIXA...")
        
        try:
            # Coleta apenas o concurso atual
            df = await fetch_caixa_data(to_latest=False)
            print(f"\nDados coletados:")
            print(df.to_string())
            
            # Verifica se snapshots foram criados
            logs_dir = Path("logs/html")
            snapshots = list(logs_dir.glob("*.txt"))
            print(f"\nSnapshots salvos: {len(snapshots)}")
            for snapshot in snapshots[-3:]:  # Mostra últimos 3
                print(f"  {snapshot.name}")
                
        except Exception as e:
            print(f"Erro: {e}")
    
    # Executa o teste
    asyncio.run(main())