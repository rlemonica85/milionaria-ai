"""Módulo ETL para extrair dados limpos do banco de dados.

Este módulo fornece funcionalidades para carregar dados dos sorteios
da +Milionária em formato limpo para análise e modelagem de IA.
"""

import sqlite3
from pathlib import Path
from typing import Union
import polars as pl
from datetime import date


def load_draws(db_path: Union[str, Path]) -> pl.DataFrame:
    """Carrega dados dos sorteios do banco de dados em formato limpo.
    
    Esta função extrai todos os sorteios da tabela 'sorteios' e retorna
    um DataFrame Polars com colunas padronizadas para uso em análises
    e modelos de IA.
    
    Args:
        db_path (Union[str, Path]): Caminho para o arquivo do banco SQLite
        
    Returns:
        pl.DataFrame: DataFrame com colunas:
            - concurso (int): Número do concurso
            - data (date): Data do sorteio como objeto date
            - D1, D2, D3, D4, D5, D6 (int): Dezenas sorteadas (1-50)
            - T1, T2 (int): Trevos sorteados (1-6)
            
    Raises:
        FileNotFoundError: Se o arquivo do banco não existir
        sqlite3.Error: Se houver erro na consulta SQL
        
    Example:
        >>> df = load_draws("db/milionaria.db")
        >>> print(df.head())
        >>> print(f"Total de sorteios: {len(df)}")
    """
    db_path = Path(db_path)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")
    
    try:
        # Conecta ao banco SQLite
        conn = sqlite3.connect(str(db_path))
        
        # Query SQL para extrair todos os dados
        query = """
        SELECT 
            concurso,
            data,
            d1, d2, d3, d4, d5, d6,
            t1, t2
        FROM sorteios 
        ORDER BY concurso
        """
        
        # Executa a query e carrega em DataFrame Polars
        df = pl.read_database(
            query=query,
            connection=conn,
            schema_overrides={
                "concurso": pl.Int32,
                "data": pl.String,  # Carrega como string primeiro
                "d1": pl.Int8, "d2": pl.Int8, "d3": pl.Int8,
                "d4": pl.Int8, "d5": pl.Int8, "d6": pl.Int8,
                "t1": pl.Int8, "t2": pl.Int8
            }
        )
        
        # Converte a coluna data de string para Date
        df = df.with_columns(
            pl.col("data").str.to_date("%Y-%m-%d").alias("data")
        )
        
        # Renomeia colunas para formato padronizado
        df = df.rename({
            "d1": "D1", "d2": "D2", "d3": "D3",
            "d4": "D4", "d5": "D5", "d6": "D6",
            "t1": "T1", "t2": "T2"
        })
        
        conn.close()
        
        return df
        
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Erro ao acessar banco de dados: {e}")
    except Exception as e:
        raise Exception(f"Erro inesperado ao carregar dados: {e}")


if __name__ == "__main__":
    # Teste básico da função
    try:
        df = load_draws("db/milionaria.db")
        print("=== Dados dos Sorteios da +Milionária ===")
        print(f"Total de registros: {len(df)}")
        print(f"Colunas: {df.columns}")
        print("\n=== Primeiros 5 registros ===")
        print(df.head())
        print("\n=== Tipos das colunas ===")
        print(df.dtypes)
        print("\n=== Estatísticas básicas ===")
        print(df.describe())
        
    except Exception as e:
        print(f"Erro no teste: {e}")