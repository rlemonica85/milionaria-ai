#!/usr/bin/env python3
"""Módulo para logging e métricas de observabilidade."""

import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class MetricsLogger:
    """Classe para logging de métricas de execução."""
    
    def __init__(self, metrics_file: str = "logs/metrics.csv"):
        self.metrics_file = Path(metrics_file)
        self.start_time: Optional[float] = None
        
        # Garante que o diretório existe
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializa o arquivo CSV se não existir
        self._init_csv_file()
    
    def _init_csv_file(self):
        """Inicializa o arquivo CSV com cabeçalhos se não existir."""
        if not self.metrics_file.exists():
            with open(self.metrics_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['data_hora', 'fonte', 'concursos_novos', 'duracao_segundos', 'status'])
    
    def start_execution(self):
        """Marca o início da execução."""
        self.start_time = time.time()
    
    def log_execution(self, fonte: str, concursos_novos: int, status: str):
        """Registra uma execução no arquivo de métricas.
        
        Args:
            fonte: Nome da fonte de dados (ex: 'CaixaProvider', 'ExternalApiProvider')
            concursos_novos: Número de concursos novos coletados
            status: Status da execução ('SUCCESS', 'FAILED', 'PENDING_REVIEW')
        """
        if self.start_time is None:
            duracao = 0.0
        else:
            duracao = time.time() - self.start_time
        
        data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Append ao arquivo CSV
        with open(self.metrics_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([data_hora, fonte, concursos_novos, f"{duracao:.2f}", status])


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configura um logger com formatação padrão.
    
    Args:
        name: Nome do logger
        level: Nível de logging (default: INFO)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evita duplicação de handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Formatação
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger