"""Módulo para scoring de números da +Milionária usando machine learning.

Este módulo implementa um sistema de scoring baseado em Ridge regression
para calcular probabilidades de cada número aparecer no próximo sorteio.
"""

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from typing import Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


def learn_weights_ridge(
    history_feats: pl.DataFrame,
    alpha: float = 1.0,
    random_state: int = 42
) -> Tuple[Ridge, StandardScaler, Dict[str, float]]:
    """
    Aprende pesos das features usando Ridge regression.
    
    Args:
        history_feats: DataFrame com features históricas incluindo y_next
        alpha: Parâmetro de regularização do Ridge
        random_state: Seed para reprodutibilidade
        
    Returns:
        Tuple contendo:
        - modelo Ridge treinado
        - scaler para normalização
        - pesos default como fallback
        
    Example:
        >>> from src.etl.from_db import load_draws
        >>> from src.features.make import build_number_features
        >>> df = load_draws("db/milionaria.db")
        >>> features = build_number_features(df)
        >>> model, scaler, defaults = learn_weights_ridge(features)
    """
    # Pesos default como fallback
    default_weights = {
        'freq_total': 0.3,
        'roll10': 0.25,
        'roll25': 0.2,
        'last_seen': -0.15,  # Sinal invertido: quanto maior, menor o score
        'momentum5': 0.2
    }
    
    # Preparar dados para treinamento
    feature_cols = ['freq_total', 'roll10', 'roll25', 'last_seen', 'momentum5']
    
    # Filtrar apenas dados com y_next válido
    train_data = history_feats.filter(pl.col('y_next').is_not_null())
    
    if len(train_data) == 0:
        print("Aviso: Nenhum dado de treino disponível, usando pesos default")
        # Retorna modelo dummy
        model = Ridge(alpha=alpha, random_state=random_state)
        scaler = StandardScaler()
        return model, scaler, default_weights
    
    # Extrair features e target
    X = train_data.select(feature_cols).to_numpy()
    y = train_data.select('y_next').to_numpy().ravel().astype(int)
    
    # Normalizar features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Treinar modelo Ridge
    model = Ridge(alpha=alpha, random_state=random_state)
    model.fit(X_scaled, y)
    
    # Blend com pesos default (70% modelo, 30% default)
    learned_weights = dict(zip(feature_cols, model.coef_))
    blended_weights = {}
    
    for feature in feature_cols:
        learned_w = learned_weights.get(feature, 0.0)
        default_w = default_weights.get(feature, 0.0)
        blended_weights[feature] = 0.7 * learned_w + 0.3 * default_w
    
    print(f"Modelo treinado com {len(train_data)} amostras")
    print(f"Score R² do modelo: {model.score(X_scaled, y):.4f}")
    
    return model, scaler, blended_weights


def score_numbers(
    snapshot: pl.DataFrame,
    weights: Dict[str, float],
    normalize: bool = True
) -> Dict[int, float]:
    """
    Calcula scores para cada número baseado nas features e pesos.
    
    Args:
        snapshot: DataFrame com features do último sorteio (sem y_next)
        weights: Dicionário com pesos para cada feature
        normalize: Se True, normaliza scores para [0,1]
        
    Returns:
        Dicionário {numero: score} para dezenas (1-50)
        
    Example:
        >>> from src.etl.from_db import load_draws
        >>> from src.features.make import latest_feature_snapshot
        >>> df = load_draws("db/milionaria.db")
        >>> snapshot = latest_feature_snapshot(df)
        >>> weights = {'freq_total': 0.3, 'roll10': 0.25, 'roll25': 0.2, 'last_seen': -0.15, 'momentum5': 0.2}
        >>> scores = score_numbers(snapshot, weights)
        >>> print(f"Top número: {max(scores, key=scores.get)} com score {max(scores.values()):.4f}")
    """
    # Filtrar apenas dezenas (1-50)
    dezenas_snapshot = snapshot.filter(pl.col('tipo') == 'dezena')
    
    if len(dezenas_snapshot) != 50:
        raise ValueError(f"Esperado 50 dezenas, encontrado {len(dezenas_snapshot)}")
    
    # Calcular score para cada dezena
    scores = {}
    feature_cols = ['freq_total', 'roll10', 'roll25', 'last_seen', 'momentum5']
    
    for row in dezenas_snapshot.iter_rows(named=True):
        numero = int(row['n'])
        score = 0.0
        
        for feature in feature_cols:
            if feature in weights and feature in row:
                # Converter valor para float, tratando diferentes tipos
                raw_value = row[feature]
                if raw_value is None:
                    continue
                    
                try:
                    value = float(raw_value)
                except (ValueError, TypeError) as e:
                    # Verificar se é o erro específico com 'dezena'
                    if isinstance(raw_value, str) and 'dezena' in raw_value:
                        print(f"ERRO CRÍTICO: Tentativa de converter string '{raw_value}' contendo 'dezena' para float")
                        print(f"Feature: {feature}, Linha: {row}")
                        raise ValueError(f"Dados corrompidos detectados: '{raw_value}' não deveria estar em feature numérica '{feature}'")
                    else:
                        print(f"Aviso: Não foi possível converter {feature}={raw_value} para float: {e}")
                        continue
                    
                weight = weights[feature]
                
                # Inverter sinal para last_seen (quanto maior, pior)
                if feature == 'last_seen':
                    # Transformar: 999 -> 0, 0 -> 1
                    if value >= 999:
                        value = 0.0
                    elif value <= -1:
                        # Proteger contra divisão por zero
                        value = 1.0
                    else:
                        value = 1.0 / (1.0 + value)
                
                score += weight * value
        
        scores[numero] = score
    
    # Normalizar scores para [0,1] se solicitado
    if normalize and scores:
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        if max_score > min_score:
            for numero in scores:
                scores[numero] = (scores[numero] - min_score) / (max_score - min_score)
        else:
            # Todos os scores são iguais
            for numero in scores:
                scores[numero] = 0.5
    
    return scores


def print_top_scores(scores: Dict[int, float], top_k: int = 10) -> None:
    """
    Imprime os top-K números com maiores scores.
    
    Args:
        scores: Dicionário {numero: score}
        top_k: Quantidade de números para mostrar
    """
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n=== Top {top_k} Números por Score ===")
    print("Pos | Número | Score")
    print("-" * 20)
    
    for i, (numero, score) in enumerate(sorted_scores[:top_k], 1):
        print(f"{i:2d}  | {numero:2d}     | {score:.4f}")


if __name__ == "__main__":
    # Teste do módulo
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from src.etl.from_db import load_draws
    from src.features.make import build_number_features, latest_feature_snapshot
    
    print("=== Teste do Módulo Scoring ===")
    
    # Carregar dados
    df = load_draws("db/milionaria.db")
    print(f"Dados carregados: {len(df)} sorteios")
    
    # Gerar features
    features = build_number_features(df)
    snapshot = latest_feature_snapshot(df)
    print(f"Features: {len(features)} linhas, Snapshot: {len(snapshot)} linhas")
    
    # Treinar modelo
    print("\n=== Treinando Modelo Ridge ===")
    model, scaler, weights = learn_weights_ridge(features)
    
    print("\nPesos aprendidos (blended):")
    for feature, weight in weights.items():
        print(f"  {feature}: {weight:.4f}")
    
    # Calcular scores
    print("\n=== Calculando Scores ===")
    scores = score_numbers(snapshot, weights)
    
    print(f"Scores calculados para {len(scores)} dezenas")
    print(f"Score mínimo: {min(scores.values()):.4f}")
    print(f"Score máximo: {max(scores.values()):.4f}")
    print(f"Score médio: {np.mean(list(scores.values())):.4f}")
    
    # Verificar determinismo
    scores2 = score_numbers(snapshot, weights)
    is_deterministic = scores == scores2
    print(f"\nDeterminístico: {is_deterministic}")
    
    # Mostrar top-10
    print_top_scores(scores, top_k=10)
    
    print("\n=== Verificações ===")
    print(f"✓ Retorna dicionário: {isinstance(scores, dict)}")
    print(f"✓ Contém 50 scores: {len(scores) == 50}")
    print(f"✓ Números 1-50: {set(scores.keys()) == set(range(1, 51))}")
    print(f"✓ Determinístico: {is_deterministic}")
    print(f"✓ Scores normalizados [0,1]: {all(0 <= s <= 1 for s in scores.values())}")