#!/usr/bin/env python3
"""Módulo para atualização automática do banco de dados da +Milionária."""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.db.io import read_max_concurso, upsert_rows
from src.db.schema import ensure_schema, get_engine
from src.update.fetch_caixa import CaixaFetcher
from src.utils.validate import sanity_checks
from src.utils.metrics import MetricsLogger, setup_logger

# Configura logger
logger = setup_logger(__name__)


async def update_database():
    """Atualiza o banco de dados com novos concursos da +Milionária.
    
    Returns:
        tuple: (ultimo_concurso, novos_concursos)
    """
    metrics = MetricsLogger()
    metrics.start_execution()
    
    logger.info("Iniciando atualizacao do banco de dados...")
    print("Iniciando atualizacao do banco de dados...")
    
    # Garante que o schema existe
    engine = get_engine()
    ensure_schema(engine)
    
    # Lê o máximo concurso atual
    max_concurso = read_max_concurso()
    logger.info(f"Ultimo concurso no banco: {max_concurso if max_concurso > 0 else 'Nenhum'}")
    print(f"Ultimo concurso no banco: {max_concurso if max_concurso > 0 else 'Nenhum'}")
    
    # Usa o fetcher com context manager
    async with CaixaFetcher() as fetcher:
        try:
            if max_concurso == 0:
                # Se não há dados, busca tudo
                logger.info("Buscando todos os concursos disponiveis...")
                print("Buscando todos os concursos disponiveis...")
                df = await fetcher.fetch_range()
            else:
                # Busca apenas concursos novos
                start_concurso = max_concurso + 1
                logger.info(f"Buscando concursos a partir do {start_concurso}...")
                print(f"Buscando concursos a partir do {start_concurso}...")
                df = await fetcher.fetch_range(start_concurso=start_concurso)
            
            if df.empty:
                logger.info("Nenhum concurso novo encontrado.")
                print("Nenhum concurso novo encontrado.")
                ultimo_concurso = max_concurso
                novos_concursos = 0
            else:
                # Grava os novos dados
                logger.info(f"Salvando {len(df)} novos concursos...")
                print(f"Salvando {len(df)} novos concursos...")
                rows_affected = upsert_rows(df)
                
                # Calcula estatísticas
                ultimo_concurso = df['concurso'].max()
                novos_concursos = len(df)
                
                logger.info(f"Atualizado ate concurso {ultimo_concurso}. Novos: {novos_concursos}")
                print(f"Atualizado ate concurso {ultimo_concurso}. Novos: {novos_concursos}")
            
            # Executar checks de integridade após a atualização (sempre)
            logger.info("Executando verificacoes de integridade...")
            print("\nExecutando verificacoes de integridade...")
            try:
                sanity_checks()
                logger.info("Verificacoes de integridade aprovadas!")
                print("Verificacoes de integridade aprovadas!")
            except Exception as e:
                logger.error(f"Erro na verificacao de integridade: {e}")
                print(f"Erro na verificacao de integridade: {e}")
                metrics.log_execution('CaixaFetcher', novos_concursos, 'FAILED')
                raise
            
            # Log de sucesso
            metrics.log_execution('CaixaFetcher', novos_concursos, 'SUCCESS')
            return ultimo_concurso, novos_concursos
            
        except Exception as e:
             error_msg = str(e)
             if "Não foi possível encontrar concurso" in error_msg:
                 logger.info("Nenhum concurso novo encontrado.")
                 print("Nenhum concurso novo encontrado.")
                 ultimo_concurso = max_concurso
                 novos_concursos = 0
                 
                 # Executar checks de integridade mesmo quando não há novos concursos
                 logger.info("Executando verificacoes de integridade...")
                 print("\nExecutando verificacoes de integridade...")
                 try:
                     sanity_checks()
                     logger.info("Verificacoes de integridade aprovadas!")
                     print("Verificacoes de integridade aprovadas!")
                 except Exception as validation_error:
                     logger.error(f"Erro na verificacao de integridade: {validation_error}")
                     print(f"Erro na verificacao de integridade: {validation_error}")
                     metrics.log_execution('CaixaFetcher', 0, 'FAILED')
                     raise
                 
                 # Log de sucesso mesmo sem novos concursos
                 metrics.log_execution('CaixaFetcher', 0, 'SUCCESS')
                 return ultimo_concurso, novos_concursos
             else:
                 logger.error(f"Erro durante a atualizacao: {e}")
                 print(f"Erro durante a atualizacao: {e}")
                 metrics.log_execution('CaixaFetcher', 0, 'FAILED')
                 raise


async def main():
    """Função principal para execução do módulo."""
    try:
        ultimo, novos = await update_database()
        print(f"\nResumo da atualizacao:")
        print(f"   • Último concurso: {ultimo}")
        print(f"   • Novos concursos: {novos}")
        return 0
    except Exception as e:
        print(f"\nFalha na atualizacao: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)