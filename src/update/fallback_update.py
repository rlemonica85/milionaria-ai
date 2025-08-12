#!/usr/bin/env python3
"""Sistema de fallback para atualização robusta da +Milionária."""

import asyncio
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd
from datetime import datetime
from pathlib import Path

from .provider_base import DataProvider
from .caixa_provider import CaixaProvider
from .external_api_provider import ExternalApiProvider
from ..utils.metrics import MetricsLogger, setup_logger

# Configura logger
logger = setup_logger(__name__)


class FallbackUpdateResult:
    """Resultado de uma atualização com fallback."""
    
    def __init__(self):
        self.success = False
        self.data: Optional[pd.DataFrame] = None
        self.source_used: Optional[str] = None
        self.providers_tried: List[str] = []
        self.errors: Dict[str, str] = {}
        self.has_divergence = False
        self.divergence_details: Optional[str] = None
        self.status = "FAILED"  # FAILED, SUCCESS, PENDING_REVIEW
    
    def __str__(self) -> str:
        return f"FallbackUpdateResult(status={self.status}, source={self.source_used}, records={len(self.data) if self.data is not None else 0})"


class FallbackUpdater:
    """Sistema de atualização com fallback entre múltiplos providers.
    
    Implementa estratégia de cascata:
    1. Tenta CaixaProvider (fonte oficial)
    2. Se falhar, tenta ExternalApiProvider
    3. Se ambos funcionarem mas divergirem, marca PENDING REVIEW
    4. Logs detalhados de qual fonte foi usada
    """
    
    def __init__(self, enable_divergence_check: bool = True):
        """Inicializa o FallbackUpdater.
        
        Args:
            enable_divergence_check (bool): Se deve verificar divergências entre providers
        """
        self.enable_divergence_check = enable_divergence_check
        self.providers: List[DataProvider] = []
        self._setup_providers()
        
        # Cria diretório para logs de fallback
        self.logs_dir = Path("logs/fallback")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_providers(self) -> None:
        """Configura os providers em ordem de prioridade."""
        self.providers = [
            CaixaProvider(headless=True, timeout=30000),
            ExternalApiProvider()
        ]
        
        # Ordena por prioridade (menor número = maior prioridade)
        self.providers.sort(key=lambda p: p.priority)
        
        print(f"Providers configurados: {[str(p) for p in self.providers]}")
    
    async def update(self, start_concurso: Optional[int] = None) -> FallbackUpdateResult:
        """Executa atualização com fallback entre providers.
        
        Args:
            start_concurso (Optional[int]): Concurso inicial para coleta
        
        Returns:
            FallbackUpdateResult: Resultado da atualização
        """
        result = FallbackUpdateResult()
        metrics = MetricsLogger()
        metrics.start_execution()
        
        logger.info("Iniciando atualização com sistema de fallback")
        print("Iniciando atualização com sistema de fallback...")
        print(f"Providers disponíveis: {len(self.providers)}")
        
        # Tenta cada provider em ordem de prioridade
        successful_results: List[Tuple[DataProvider, pd.DataFrame]] = []
        
        for provider in self.providers:
            logger.info(f"Tentando provider: {provider.name}")
            print(f"\nTentando provider: {provider.name}")
            result.providers_tried.append(provider.name)
            
            try:
                # Verifica disponibilidade
                if not await provider.is_available():
                    error_msg = f"{provider.name} não está disponível"
                    logger.warning(error_msg)
                    print(error_msg)
                    result.errors[provider.name] = error_msg
                    continue
                
                # Tenta coletar dados
                data = await provider.fetch(start_concurso)
                
                if data is not None and not data.empty:
                    logger.info(f"{provider.name} coletou {len(data)} registros com sucesso")
                    print(f"✓ {provider.name} coletou {len(data)} registros com sucesso")
                    successful_results.append((provider, data))
                    
                    # Se é o primeiro sucesso, usa como resultado principal
                    if not result.success:
                        result.success = True
                        result.data = data
                        result.source_used = provider.name
                        result.status = "SUCCESS"
                        logger.info(f"Fonte principal definida: {provider.name}")
                        print(f"Fonte principal definida: {provider.name}")
                else:
                    error_msg = f"{provider.name} retornou dados vazios"
                    logger.warning(error_msg)
                    print(error_msg)
                    result.errors[provider.name] = error_msg
                    
            except Exception as e:
                error_msg = f"Erro em {provider.name}: {str(e)}"
                logger.error(error_msg)
                print(error_msg)
                result.errors[provider.name] = error_msg
        
        # Verifica divergências se habilitado e há múltiplos sucessos
        if self.enable_divergence_check and len(successful_results) > 1:
            await self._check_divergences(result, successful_results)
        
        # Log do resultado final
        await self._log_result(result, start_concurso)
        
        # Log de métricas
        if result.success:
            metrics.log_execution(result.source_used, len(result.data), result.status)
        else:
            metrics.log_execution('FALLBACK_SYSTEM', 0, 'FAILED')
        
        # Imprime fonte usada conforme solicitado
        if result.success:
            logger.info(f"FONTE USADA: {result.source_used}, REGISTROS: {len(result.data)}, STATUS: {result.status}")
            print(f"\n🎯 FONTE USADA: {result.source_used}")
            print(f"📊 REGISTROS COLETADOS: {len(result.data)}")
            print(f"📋 STATUS: {result.status}")
        else:
            logger.error("FALHA: Nenhum provider conseguiu coletar dados")
            print("\n❌ FALHA: Nenhum provider conseguiu coletar dados")
            print(f"📋 STATUS: {result.status}")
        
        return result
    
    async def _check_divergences(
        self, 
        result: FallbackUpdateResult, 
        successful_results: List[Tuple[DataProvider, pd.DataFrame]]
    ) -> None:
        """Verifica divergências entre resultados de diferentes providers.
        
        Args:
            result (FallbackUpdateResult): Resultado sendo construído
            successful_results (List): Lista de (provider, dataframe) bem-sucedidos
        """
        print("\nVerificando divergências entre providers...")
        
        if len(successful_results) < 2:
            return
        
        # Compara o primeiro com os demais
        primary_provider, primary_data = successful_results[0]
        
        for secondary_provider, secondary_data in successful_results[1:]:
            divergences = self._compare_dataframes(primary_data, secondary_data)
            
            if divergences:
                result.has_divergence = True
                result.status = "PENDING_REVIEW"
                
                divergence_msg = (
                    f"DIVERGÊNCIA detectada entre {primary_provider.name} e {secondary_provider.name}:\n"
                    f"{divergences}"
                )
                
                result.divergence_details = divergence_msg
                logger.warning(f"DIVERGÊNCIA detectada: {divergence_msg}")
                print(f"⚠️  {divergence_msg}")
                
                # Não grava dados quando há divergência
                print("🚫 Dados NÃO serão gravados devido à divergência")
                break
    
    def _compare_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Optional[str]:
        """Compara dois DataFrames e retorna descrição das divergências.
        
        Args:
            df1 (pd.DataFrame): Primeiro DataFrame
            df2 (pd.DataFrame): Segundo DataFrame
        
        Returns:
            Optional[str]: Descrição das divergências ou None se são iguais
        """
        divergences = []
        
        # Compara número de registros
        if len(df1) != len(df2):
            divergences.append(f"Número de registros: {len(df1)} vs {len(df2)}")
        
        # Compara concursos presentes
        concursos1 = set(df1['concurso'].tolist())
        concursos2 = set(df2['concurso'].tolist())
        
        if concursos1 != concursos2:
            only_in_1 = concursos1 - concursos2
            only_in_2 = concursos2 - concursos1
            
            if only_in_1:
                divergences.append(f"Concursos apenas no primeiro: {sorted(only_in_1)}")
            if only_in_2:
                divergences.append(f"Concursos apenas no segundo: {sorted(only_in_2)}")
        
        # Para concursos em comum, compara dados
        common_concursos = concursos1 & concursos2
        for concurso in common_concursos:
            row1 = df1[df1['concurso'] == concurso].iloc[0]
            row2 = df2[df2['concurso'] == concurso].iloc[0]
            
            # Compara dezenas e trevos
            for col in ['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 't1', 't2']:
                if row1[col] != row2[col]:
                    divergences.append(
                        f"Concurso {concurso}, {col}: {row1[col]} vs {row2[col]}"
                    )
        
        return "\n".join(divergences) if divergences else None
    
    async def _log_result(self, result: FallbackUpdateResult, start_concurso: Optional[int]) -> None:
        """Salva log detalhado do resultado.
        
        Args:
            result (FallbackUpdateResult): Resultado da atualização
            start_concurso (Optional[int]): Concurso inicial solicitado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fallback_{timestamp}.log"
        filepath = self.logs_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Fallback Update Log\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Start Concurso: {start_concurso}\n")
                f.write(f"Status: {result.status}\n")
                f.write(f"Success: {result.success}\n")
                f.write(f"Source Used: {result.source_used}\n")
                f.write(f"Records: {len(result.data) if result.data is not None else 0}\n")
                f.write(f"Has Divergence: {result.has_divergence}\n")
                f.write("\n" + "="*50 + "\n")
                
                f.write(f"Providers Tried: {', '.join(result.providers_tried)}\n\n")
                
                if result.errors:
                    f.write("Errors:\n")
                    for provider, error in result.errors.items():
                        f.write(f"  {provider}: {error}\n")
                    f.write("\n")
                
                if result.has_divergence and result.divergence_details:
                    f.write("Divergence Details:\n")
                    f.write(result.divergence_details)
                    f.write("\n\n")
                
                if result.data is not None:
                    f.write("Data Summary:\n")
                    f.write(f"  Shape: {result.data.shape}\n")
                    if not result.data.empty:
                        f.write(f"  Concursos: {result.data['concurso'].min()} - {result.data['concurso'].max()}\n")
                        f.write(f"  Sample:\n{result.data.head().to_string(index=False)}\n")
        
        except Exception as e:
            print(f"Erro ao salvar log de fallback: {e}")


# Função de conveniência
async def update_with_fallback(start_concurso: Optional[int] = None) -> FallbackUpdateResult:
    """Função de conveniência para atualização com fallback.
    
    Args:
        start_concurso (Optional[int]): Concurso inicial para coleta
    
    Returns:
        FallbackUpdateResult: Resultado da atualização
    """
    updater = FallbackUpdater()
    return await updater.update(start_concurso)


if __name__ == "__main__":
    # Teste básico
    async def main():
        print("Testando sistema de fallback...")
        result = await update_with_fallback()
        print(f"\nResultado final: {result}")
    
    asyncio.run(main())