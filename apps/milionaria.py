#!/usr/bin/env python3
"""
Milionária AI - CLI Principal

Interface de linha de comando para operações de importação e atualização
de dados da Mega da Virada.

Uso:
    python milionaria.py --import <arquivo>  # Importar dados iniciais
    python milionaria.py --update           # Atualizar dados via web scraping

Exemplos:
    python milionaria.py --import data/raw/base_275.xlsx
    python milionaria.py --update
"""

import argparse
import sys
import os
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Importações do projeto
from ingest.import_initial import load_and_process_excel
from update.update_db import update_database
from db.io import upsert_rows
from db.schema import ensure_schema, get_engine
import asyncio


def setup_logging():
    """Configura logging para o CLI"""
    import logging
    
    # Criar diretório de logs se não existir
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'milionaria_cli.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def cmd_import(file_path: str, logger) -> int:
    """Executa importação de dados iniciais
    
    Args:
        file_path: Caminho para o arquivo Excel
        logger: Logger configurado
        
    Returns:
        0 se sucesso, 1 se erro
    """
    try:
        logger.info(f"Iniciando importação de {file_path}")
        
        # Verificar se arquivo existe
        if not Path(file_path).exists():
            logger.error(f"Arquivo não encontrado: {file_path}")
            return 1
        
        # Carrega e processa a planilha
        df = load_and_process_excel(file_path)
        
        # Garante que o banco e schema existem
        logger.info("Preparando banco de dados...")
        engine = get_engine()
        ensure_schema(engine)
        
        # Importa os dados
        logger.info("Importando dados para o banco...")
        rows_affected = upsert_rows(df)
        
        logger.info(f"✅ Importação concluída: {len(df)} linhas processadas, {rows_affected} afetadas")
        return 0
            
    except Exception as e:
        logger.error(f"❌ Erro durante importação: {str(e)}")
        return 1


def cmd_update(logger) -> int:
    """Executa atualização de dados via web scraping
    
    Args:
        logger: Logger configurado
        
    Returns:
        0 se sucesso, 1 se erro
    """
    try:
        logger.info("Iniciando atualização de dados")
        
        # Executar atualização assíncrona
        ultimo, novos = asyncio.run(update_database())
        
        logger.info(f"✅ Atualização concluída: último concurso {ultimo}, {novos} novos concursos")
        return 0
            
    except Exception as e:
        logger.error(f"❌ Erro durante atualização: {str(e)}")
        return 1


def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description='Milionária AI - Gerenciador de dados da Mega da Virada',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s --import data/raw/base_275.xlsx    # Importar dados iniciais
  %(prog)s --update                          # Atualizar dados via web
        """
    )
    
    # Grupo mutuamente exclusivo para as operações
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        '--import',
        dest='import_file',
        metavar='ARQUIVO',
        help='Importar dados iniciais de arquivo Excel'
    )
    
    group.add_argument(
        '--update',
        action='store_true',
        help='Atualizar dados via web scraping'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Milionária AI v1.0.0'
    )
    
    # Parse dos argumentos
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Executar comando apropriado
    if args.import_file:
        return cmd_import(args.import_file, logger)
    elif args.update:
        return cmd_update(logger)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())