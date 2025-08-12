#!/usr/bin/env python3
"""Provider para coleta de dados da CAIXA usando Playwright."""

from typing import Optional
import pandas as pd
from .provider_base import DataProvider
from .fetch_caixa import CaixaFetcher, FetchError


class CaixaProvider(DataProvider):
    """Provider para coleta de dados da +Milionária diretamente do site da CAIXA.
    
    Utiliza o CaixaFetcher existente que usa Playwright para navegar
    no site oficial e extrair os dados dos sorteios.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """Inicializa o CaixaProvider.
        
        Args:
            headless (bool): Se deve executar o browser em modo headless
            timeout (int): Timeout em milissegundos para operações do browser
        """
        self.headless = headless
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        """Nome identificador do provider."""
        return "CaixaProvider"
    
    @property
    def priority(self) -> int:
        """Prioridade do provider (0 = mais alta)."""
        return 0  # Prioridade mais alta - fonte oficial
    
    async def is_available(self) -> bool:
        """Verifica se o site da CAIXA está disponível.
        
        Tenta fazer uma conexão básica com o site para verificar
        se está acessível antes de tentar coletar dados.
        """
        try:
            async with CaixaFetcher(headless=self.headless, timeout=5000) as fetcher:
                # Tenta carregar a página principal
                await fetcher._load_page()
                return True
        except Exception as e:
            print(f"CaixaProvider indisponível: {e}")
            return False
    
    async def fetch(self, start_concurso: Optional[int] = None) -> pd.DataFrame:
        """Coleta dados de concursos da +Milionária do site da CAIXA.
        
        Args:
            start_concurso (Optional[int]): Concurso inicial para coleta.
                                          Se None, coleta a partir do concurso atual.
        
        Returns:
            pd.DataFrame: DataFrame com dados dos concursos
        
        Raises:
            Exception: Se não conseguir coletar os dados
        """
        try:
            print(f"Coletando dados via {self.name}...")
            
            async with CaixaFetcher(headless=self.headless, timeout=self.timeout) as fetcher:
                df = await fetcher.fetch_range(
                    start_concurso=start_concurso,
                    to_latest=True
                )
                
                # Valida os dados coletados
                if not await self.validate_data(df):
                    raise FetchError("Dados coletados são inválidos")
                
                print(f"CaixaProvider coletou {len(df)} concursos com sucesso")
                return df
                
        except Exception as e:
            error_msg = f"Erro no CaixaProvider: {e}"
            print(error_msg)
            raise Exception(error_msg) from e