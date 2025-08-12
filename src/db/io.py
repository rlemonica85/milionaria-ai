"""Módulo para operações de entrada/saída do banco de dados."""

import pandas as pd
from sqlalchemy import text
from .schema import get_engine


def upsert_rows(df, db_path="db/milionaria.db"):
    """Insere ou atualiza linhas na tabela sorteios sem duplicar concurso.
    
    Args:
        df (pandas.DataFrame): DataFrame com colunas: concurso, data, d1-d6, t1, t2
        db_path (str): Caminho para o arquivo do banco de dados
        
    Returns:
        int: Número de linhas afetadas
    """
    engine = get_engine(db_path)
    
    # Valida colunas obrigatórias
    required_cols = ['concurso', 'data', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 't1', 't2']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
    
    # Seleciona apenas as colunas necessárias
    df_clean = df[required_cols].copy()
    
    # Remove duplicatas no DataFrame baseado em 'concurso'
    df_clean = df_clean.drop_duplicates(subset=['concurso'], keep='last')
    
    rows_affected = 0
    
    with engine.connect() as conn:
        # Para cada linha, faz upsert (INSERT OR REPLACE no SQLite)
        for _, row in df_clean.iterrows():
            query = text("""
                INSERT OR REPLACE INTO sorteios 
                (concurso, data, d1, d2, d3, d4, d5, d6, t1, t2)
                VALUES (:concurso, :data, :d1, :d2, :d3, :d4, :d5, :d6, :t1, :t2)
            """)
            
            # Converte data para string se for Timestamp
            data_value = row['data']
            if hasattr(data_value, 'strftime'):
                data_value = data_value.strftime('%Y-%m-%d')
            
            result = conn.execute(query, {
                'concurso': int(row['concurso']),
                'data': data_value,
                'd1': int(row['d1']),
                'd2': int(row['d2']),
                'd3': int(row['d3']),
                'd4': int(row['d4']),
                'd5': int(row['d5']),
                'd6': int(row['d6']),
                't1': int(row['t1']),
                't2': int(row['t2'])
            })
            rows_affected += result.rowcount
        
        conn.commit()
    
    print(f"Upsert concluído: {rows_affected} linhas afetadas")
    return rows_affected


def read_max_concurso(db_path="db/milionaria.db"):
    """Retorna o número do concurso máximo na tabela sorteios.
    
    Args:
        db_path (str): Caminho para o arquivo do banco de dados
        
    Returns:
        int: Número do concurso máximo, ou 0 se tabela vazia
    """
    engine = get_engine(db_path)
    
    with engine.connect() as conn:
        query = text("SELECT MAX(concurso) as max_concurso FROM sorteios")
        result = conn.execute(query)
        row = result.fetchone()
        
        max_concurso = row[0] if row[0] is not None else 0
        return max_concurso


def read_all_sorteios(db_path="db/milionaria.db"):
    """Lê todos os sorteios da tabela.
    
    Args:
        db_path (str): Caminho para o arquivo do banco de dados
        
    Returns:
        pandas.DataFrame: DataFrame com todos os sorteios
    """
    engine = get_engine(db_path)
    
    query = "SELECT * FROM sorteios ORDER BY concurso"
    df = pd.read_sql(query, engine)
    return df


if __name__ == "__main__":
    # Teste básico
    from .schema import ensure_schema
    
    engine = get_engine()
    ensure_schema(engine)
    
    # Teste com dados fictícios
    test_data = pd.DataFrame({
        'concurso': [1, 2],
        'data': ['2023-01-01', '2023-01-08'],
        'd1': [1, 5], 'd2': [2, 10], 'd3': [3, 15], 
        'd4': [4, 20], 'd5': [5, 25], 'd6': [6, 30],
        't1': [1, 2], 't2': [2, 3]
    })
    
    upsert_rows(test_data)
    max_concurso = read_max_concurso()
    print(f"Máximo concurso: {max_concurso}")