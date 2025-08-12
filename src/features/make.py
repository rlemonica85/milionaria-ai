"""Módulo para geração de features históricas da +Milionária.

Este módulo implementa funções para extrair características estatísticas
dos números sorteados, incluindo frequências, tendências temporais e
padrões de aparição para uso em modelos de machine learning.
"""

import polars as pl
from typing import Optional


def build_number_features(df: pl.DataFrame) -> pl.DataFrame:
    """Constrói features históricas para cada número em cada sorteio.
    
    Para cada combinação de (concurso, número), calcula estatísticas
    históricas baseadas nos sorteios anteriores, incluindo frequências,
    rolling windows e momentum. Adiciona rótulo y_next indicando se o
    número aparecerá no próximo sorteio.
    
    Args:
        df (pl.DataFrame): DataFrame com colunas concurso, data, D1-D6, T1-T2
        
    Returns:
        pl.DataFrame: DataFrame com colunas:
            - concurso (int): Número do concurso
            - n (int): Número analisado (1-50 para dezenas, 1-6 para trevos)
            - tipo (str): 'dezena' ou 'trevo'
            - freq_total (int): Frequência total até o concurso
            - roll10 (int): Frequência nos últimos 10 sorteios
            - roll25 (int): Frequência nos últimos 25 sorteios
            - last_seen (int): Concursos desde última aparição
            - momentum5 (float): Tendência nos últimos 5 sorteios
            - y_next (bool): Se aparece no próximo sorteio
            
    Raises:
        ValueError: Se DataFrame estiver vazio ou sem colunas necessárias
        
    Example:
        >>> from src.etl.from_db import load_draws
        >>> df = load_draws("db/milionaria.db")
        >>> features = build_number_features(df)
        >>> print(f"Features geradas: {len(features)}")
    """
    if df.is_empty():
        raise ValueError("DataFrame não pode estar vazio")
    
    required_cols = ['concurso', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
    
    # Validação adicional para detectar dados corrompidos
    try:
        # Verificar se há valores não numéricos nas colunas de números
        numeric_cols = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2']
        for col in numeric_cols:
            if col in df.columns:
                # Verificar se há strings problemáticas
                sample_values = df[col].head(10).to_list()
                for val in sample_values:
                    if isinstance(val, str) and 'dezena' in val:
                        raise ValueError(f"Dados corrompidos detectados na coluna '{col}': valor '{val}' contém 'dezena'")
                    elif val is not None:
                        try:
                            float(val)
                        except (ValueError, TypeError):
                            if isinstance(val, str) and any(char.isalpha() for char in val):
                                raise ValueError(f"Dados corrompidos na coluna '{col}': valor não numérico '{val}'")
    except Exception as validation_error:
        print(f"ERRO DE VALIDAÇÃO: {validation_error}")
        raise validation_error
    
    # Ordena por concurso para garantir ordem cronológica
    df = df.sort('concurso')
    
    # Converte dados para formato longo (unpivot)
    dezenas_df = df.select([
        'concurso',
        pl.col(['D1', 'D2', 'D3', 'D4', 'D5', 'D6'])
    ]).unpivot(
        index='concurso',
        on=['D1', 'D2', 'D3', 'D4', 'D5', 'D6'],
        variable_name='pos',
        value_name='n'
    ).with_columns(
        pl.lit('dezena').alias('tipo')
    ).select(['concurso', 'n', 'tipo'])
    
    trevos_df = df.select([
        'concurso',
        pl.col(['T1', 'T2'])
    ]).unpivot(
        index='concurso',
        on=['T1', 'T2'],
        variable_name='pos',
        value_name='n'
    ).with_columns(
        pl.lit('trevo').alias('tipo')
    ).select(['concurso', 'n', 'tipo'])
    
    # Combina dezenas e trevos
    long_df = pl.concat([dezenas_df, trevos_df])
    
    # Cria grid completo de (concurso, número, tipo)
    concursos = df.select('concurso').unique().sort('concurso')
    
    # Grid para dezenas (1-50)
    dezenas_grid = concursos.join(
        pl.DataFrame({
            'n': list(range(1, 51)),
            'tipo': ['dezena'] * 50
        }),
        how='cross'
    )
    
    # Grid para trevos (1-6)
    trevos_grid = concursos.join(
        pl.DataFrame({
            'n': list(range(1, 7)),
            'tipo': ['trevo'] * 6
        }),
        how='cross'
    )
    
    # Grid completo
    full_grid = pl.concat([dezenas_grid, trevos_grid])
    
    # Marca aparições (1 se apareceu, 0 caso contrário)
    grid_with_appearances = full_grid.join(
        long_df.with_columns(pl.lit(1).alias('apareceu')),
        on=['concurso', 'n', 'tipo'],
        how='left'
    ).with_columns(
        pl.col('apareceu').fill_null(0)
    )
    
    # Calcula features por grupo (n, tipo)
    features_df = grid_with_appearances.with_columns([
        # Frequência total acumulada até o concurso atual (exclusive)
        pl.col('apareceu').cum_sum().over(['n', 'tipo']).shift(1, fill_value=0).alias('freq_total'),
        
        # Rolling windows
        pl.col('apareceu').rolling_sum(window_size=10, min_samples=1).over(['n', 'tipo']).shift(1, fill_value=0).alias('roll10'),
        pl.col('apareceu').rolling_sum(window_size=25, min_samples=1).over(['n', 'tipo']).shift(1, fill_value=0).alias('roll25'),
        
        # Momentum (média móvel dos últimos 5)
        pl.col('apareceu').rolling_mean(window_size=5, min_samples=1).over(['n', 'tipo']).shift(1, fill_value=0.0).alias('momentum5')
    ])
    
    # Calcula last_seen (concursos desde última aparição)
    features_df = features_df.with_columns([
        pl.when(pl.col('apareceu').shift(1, fill_value=0).over(['n', 'tipo']) == 1)
        .then(0)
        .otherwise(
            pl.when(pl.col('freq_total') == 0)
            .then(999)  # Nunca apareceu
            .otherwise(
                pl.col('concurso') - 
                pl.col('concurso').filter(pl.col('apareceu') == 1).last().over(['n', 'tipo'])
            )
        ).alias('last_seen_temp')
    ])
    
    # Calcula last_seen de forma mais robusta
    features_df = features_df.with_columns([
        pl.col('concurso').rank('ordinal').over(['n', 'tipo']).alias('rank_concurso')
    ])
    
    # Para cada linha, encontra a última aparição anterior
    features_df = features_df.with_columns([
        pl.when(pl.col('freq_total') == 0)
        .then(pl.col('rank_concurso') - 1)  # Nunca apareceu antes
        .otherwise(
            pl.col('rank_concurso') - 
            pl.col('rank_concurso').filter(
                (pl.col('apareceu') == 1) & 
                (pl.col('rank_concurso') < pl.col('rank_concurso'))
            ).max().over(['n', 'tipo']).fill_null(0) - 1
        ).alias('last_seen')
    ])
    
    # Simplifica cálculo de last_seen
    features_df = features_df.with_columns([
        pl.when(pl.col('freq_total') == 0)
        .then(999)  # Nunca apareceu
        .otherwise(
            (pl.col('concurso') - 
             pl.col('concurso').filter(pl.col('apareceu') == 1).last().over(['n', 'tipo'])).fill_null(999)
        ).alias('last_seen')
    ])
    
    # Adiciona y_next (se aparece no próximo sorteio)
    features_df = features_df.with_columns([
        pl.col('apareceu').shift(-1, fill_value=0).over(['n', 'tipo']).cast(pl.Boolean).alias('y_next')
    ])
    
    # Remove linhas do último concurso (não têm y_next válido)
    max_concurso = features_df.select(pl.col('concurso').max()).item()
    features_df = features_df.filter(pl.col('concurso') < max_concurso)
    
    # Seleciona e ordena colunas finais
    result = features_df.select([
        'concurso', 'n', 'tipo', 'freq_total', 'roll10', 'roll25', 
        'last_seen', 'momentum5', 'y_next'
    ]).sort(['concurso', 'tipo', 'n'])
    
    return result


def latest_feature_snapshot(df: pl.DataFrame) -> pl.DataFrame:
    """Gera snapshot das features para o próximo sorteio.
    
    Calcula as mesmas features históricas de build_number_features(),
    mas apenas para o estado atual (último concurso), sem o rótulo y_next.
    Usado para fazer predições do próximo sorteio.
    
    Args:
        df (pl.DataFrame): DataFrame com colunas concurso, data, D1-D6, T1-T2
        
    Returns:
        pl.DataFrame: DataFrame com colunas:
            - n (int): Número analisado (1-50 para dezenas, 1-6 para trevos)
            - tipo (str): 'dezena' ou 'trevo'
            - freq_total (int): Frequência total histórica
            - roll10 (int): Frequência nos últimos 10 sorteios
            - roll25 (int): Frequência nos últimos 25 sorteios
            - last_seen (int): Concursos desde última aparição
            - momentum5 (float): Tendência nos últimos 5 sorteios
            
    Raises:
        ValueError: Se DataFrame estiver vazio ou sem colunas necessárias
        
    Example:
        >>> from src.etl.from_db import load_draws
        >>> df = load_draws("db/milionaria.db")
        >>> snapshot = latest_feature_snapshot(df)
        >>> print(f"Dezenas únicas: {len(snapshot.filter(pl.col('tipo') == 'dezena'))}")
        >>> print(f"Trevos únicos: {len(snapshot.filter(pl.col('tipo') == 'trevo'))}")
    """
    if df.is_empty():
        raise ValueError("DataFrame não pode estar vazio")
    
    required_cols = ['concurso', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
    
    # Ordena por concurso
    df = df.sort('concurso')
    
    # Converte para formato longo
    dezenas_df = df.select([
        'concurso',
        pl.col(['D1', 'D2', 'D3', 'D4', 'D5', 'D6'])
    ]).unpivot(
        index='concurso',
        on=['D1', 'D2', 'D3', 'D4', 'D5', 'D6'],
        variable_name='pos',
        value_name='n'
    ).with_columns(
        pl.lit('dezena').alias('tipo')
    ).select(['concurso', 'n', 'tipo'])
    
    trevos_df = df.select([
        'concurso',
        pl.col(['T1', 'T2'])
    ]).unpivot(
        index='concurso',
        on=['T1', 'T2'],
        variable_name='pos',
        value_name='n'
    ).with_columns(
        pl.lit('trevo').alias('tipo')
    ).select(['concurso', 'n', 'tipo'])
    
    # Combina dezenas e trevos
    long_df = pl.concat([dezenas_df, trevos_df])
    
    # Cria grid para todos os números possíveis
    dezenas_grid = pl.DataFrame({
        'n': list(range(1, 51)),
        'tipo': ['dezena'] * 50
    })
    
    trevos_grid = pl.DataFrame({
        'n': list(range(1, 7)),
        'tipo': ['trevo'] * 6
    })
    
    numbers_grid = pl.concat([dezenas_grid, trevos_grid])
    
    # Para cada número, calcula features baseadas em todo o histórico
    snapshot_features = []
    
    for row in numbers_grid.iter_rows(named=True):
        n = row['n']
        tipo = row['tipo']
        
        # Filtra aparições deste número
        appearances = long_df.filter(
            (pl.col('n') == n) & (pl.col('tipo') == tipo)
        ).sort('concurso')
        
        # Calcula features
        freq_total = len(appearances)
        
        # Rolling windows (últimos 10 e 25 sorteios)
        max_concurso = df.select(pl.col('concurso').max()).item()
        recent_10 = appearances.filter(
            pl.col('concurso') > (max_concurso - 10)
        )
        recent_25 = appearances.filter(
            pl.col('concurso') > (max_concurso - 25)
        )
        
        roll10 = len(recent_10)
        roll25 = len(recent_25)
        
        # Last seen
        if freq_total == 0:
            last_seen = 999  # Nunca apareceu
        else:
            last_appearance = appearances.select(pl.col('concurso').max()).item()
            last_seen = max_concurso - last_appearance
        
        # Momentum (últimos 5 sorteios)
        recent_5 = appearances.filter(
            pl.col('concurso') > (max_concurso - 5)
        )
        momentum5 = len(recent_5) / 5.0
        
        snapshot_features.append({
            'n': n,
            'tipo': tipo,
            'freq_total': freq_total,
            'roll10': roll10,
            'roll25': roll25,
            'last_seen': last_seen,
            'momentum5': momentum5
        })
    
    # Converte para DataFrame
    result = pl.DataFrame(snapshot_features).sort(['tipo', 'n'])
    
    return result


if __name__ == "__main__":
    # Teste básico das funções
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from src.etl.from_db import load_draws
        
        print("=== Teste do Módulo Features ===")
        
        # Carrega dados
        df = load_draws("db/milionaria.db")
        print(f"Dados carregados: {len(df)} sorteios")
        
        # Testa build_number_features
        print("\n=== Testando build_number_features ===")
        features = build_number_features(df)
        print(f"Features geradas: {len(features)} linhas")
        print(f"Colunas: {features.columns}")
        print("\nPrimeiras 10 linhas:")
        print(features.head(10))
        
        # Verifica distribuição por tipo
        print("\nDistribuição por tipo:")
        print(features.group_by('tipo').agg(pl.len().alias('count')))
        
        # Testa latest_feature_snapshot
        print("\n=== Testando latest_feature_snapshot ===")
        snapshot = latest_feature_snapshot(df)
        print(f"Snapshot gerado: {len(snapshot)} linhas")
        print(f"Colunas: {snapshot.columns}")
        
        # Verifica se tem 50 dezenas e 6 trevos
        dezenas_count = len(snapshot.filter(pl.col('tipo') == 'dezena'))
        trevos_count = len(snapshot.filter(pl.col('tipo') == 'trevo'))
        print(f"\nDezenas únicas: {dezenas_count} (esperado: 50)")
        print(f"Trevos únicos: {trevos_count} (esperado: 6)")
        
        print("\nPrimeiras 10 linhas do snapshot:")
        print(snapshot.head(10))
        
        # Verifica edge cases
        print("\n=== Verificações de Edge Cases ===")
        print(f"Features sem y_next: {features.filter(pl.col('y_next').is_null()).height}")
        print(f"Snapshot sem valores nulos: {snapshot.null_count().sum_horizontal().sum()}")
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()