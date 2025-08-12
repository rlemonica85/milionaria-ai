#!/usr/bin/env python3
"""Classe base abstrata para providers de dados da +Milionária."""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class DataProvider(ABC):
    """Classe base abstrata para providers de dados da +Milionária.
    
    Define a interface comum que todos os providers devem implementar
    para garantir consistência e permitir fallback entre diferentes fontes.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome identificador do provider.
        
        Returns:
            str: Nome do provider (ex: 'CaixaProvider', 'ExternalApiProvider')
        """
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Prioridade do provider (menor número = maior prioridade).
        
        Returns:
            int: Prioridade do provider (0 = mais alta)
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Verifica se o provider está disponível.
        
        Returns:
            bool: True se o provider está disponível e funcionando
        """
        pass
    
    @abstractmethod
    async def fetch(self, start_concurso: Optional[int] = None) -> pd.DataFrame:
        """Coleta dados de concursos da +Milionária.
        
        Args:
            start_concurso (Optional[int]): Concurso inicial para coleta.
                                          Se None, coleta a partir do concurso atual.
        
        Returns:
            pd.DataFrame: DataFrame com colunas:
                - concurso (int): Número do concurso
                - data (str): Data do sorteio no formato 'YYYY-MM-DD'
                - d1, d2, d3, d4, d5, d6 (int): Dezenas sorteadas
                - t1, t2 (int): Trevos sorteados
        
        Raises:
            Exception: Se não conseguir coletar os dados
        """
        pass
    
    async def validate_data(self, df: pd.DataFrame) -> bool:
        """Valida se os dados coletados estão no formato correto.
        
        Args:
            df (pd.DataFrame): DataFrame com dados coletados
        
        Returns:
            bool: True se os dados são válidos
        """
        if df.empty:
            return False
        
        # Verifica colunas obrigatórias
        required_columns = ['concurso', 'data', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 't1', 't2']
        if not all(col in df.columns for col in required_columns):
            return False
        
        # Verifica se há pelo menos um registro
        if len(df) == 0:
            return False
        
        # Verifica tipos básicos
        try:
            # Concurso deve ser numérico
            pd.to_numeric(df['concurso'], errors='raise')
            
            # Dezenas devem estar no intervalo [1,50]
            for col in ['d1', 'd2', 'd3', 'd4', 'd5', 'd6']:
                dezenas = pd.to_numeric(df[col], errors='raise')
                if not all((dezenas >= 1) & (dezenas <= 50)):
                    return False
            
            # Trevos devem estar no intervalo [1,6]
            for col in ['t1', 't2']:
                trevos = pd.to_numeric(df[col], errors='raise')
                if not all((trevos >= 1) & (trevos <= 6)):
                    return False
                    
        except (ValueError, TypeError):
            return False
        
        return True
    
    def __str__(self) -> str:
        """Representação string do provider."""
        return f"{self.name} (priority: {self.priority})"
    
    def __repr__(self) -> str:
        """Representação detalhada do provider."""
        return f"{self.__class__.__name__}(name='{self.name}', priority={self.priority})"