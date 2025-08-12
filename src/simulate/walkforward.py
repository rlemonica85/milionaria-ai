"""Módulo para validação walk-forward sem vazamento temporal.

Este módulo implementa validação temporal onde o modelo é treinado apenas
com dados históricos e testado em dados futuros, evitando data leakage.
"""

import numpy as np
import polars as pl
from typing import List, Dict, Tuple, Optional, Callable
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Imports condicionais para GPU
try:
    from src.models.scoring_gpu import learn_weights_gpu, score_numbers_gpu
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Fallback para CPU
from src.models.scoring import learn_weights_ridge, score_numbers


def walk_forward_validation(
    features_df: pl.DataFrame,
    min_train_size: int = 50,
    step_size: int = 1,
    max_steps: int = None,
    use_gpu: bool = False,
    verbose: bool = True
) -> List[Dict]:
    """
    Executa validação walk-forward sem vazamento temporal.
    
    Args:
        features_df: DataFrame com features incluindo 'concurso', 'n', 'tipo', 'y_next'
        min_train_size: Tamanho mínimo do conjunto de treino
        step_size: Quantos concursos avançar a cada passo
        max_steps: Máximo de passos (None = todos possíveis)
        use_gpu: Se True, usa versão GPU do scoring
        verbose: Se True, mostra progresso
        
    Returns:
        Lista de dicionários com resultados de cada passo:
        [
            {
                'step': int,
                'train_start': int,
                'train_end': int,
                'test_concurso': int,
                'test_date': str,
                'train_size': int,
                'model_r2': float,
                'predictions': Dict[int, float],  # {numero: score}
                'actual_numbers': List[int],
                'hits': int,
                'hit_rate': float,
                'top_5_hits': int,
                'top_10_hits': int,
                'weights_used': Dict[str, float]
            },
            ...
        ]
        
    Example:
        >>> from src.etl.from_db import load_draws
        >>> from src.features.make import build_number_features
        >>> df = load_draws("db/milionaria.db")
        >>> features = build_number_features(df)
        >>> results = walk_forward_validation(features, min_train_size=30)
        >>> print(f"Acertos médios: {np.mean([r['hits'] for r in results]):.2f}")
    """
    
    # Verificar se GPU está disponível quando solicitada
    if use_gpu and not GPU_AVAILABLE:
        print("Aviso: GPU não disponível, usando CPU")
        use_gpu = False
    
    # Ordenar por concurso para garantir ordem temporal
    features_sorted = features_df.sort('concurso')
    
    # Obter lista de concursos únicos
    concursos = features_sorted.select('concurso').unique().sort('concurso')['concurso'].to_list()
    
    if len(concursos) < min_train_size + 1:
        raise ValueError(f"Dados insuficientes: {len(concursos)} concursos, mínimo {min_train_size + 1}")
    
    results = []
    
    # Determinar quantos passos executar
    max_possible_steps = len(concursos) - min_train_size
    if max_steps is None:
        total_steps = max_possible_steps
    else:
        total_steps = min(max_steps, max_possible_steps)
    
    if verbose:
        print(f"Iniciando walk-forward validation:")
        print(f"  Total de concursos: {len(concursos)}")
        print(f"  Tamanho mínimo de treino: {min_train_size}")
        print(f"  Passos a executar: {total_steps}")
        print(f"  Usando {'GPU' if use_gpu else 'CPU'}")
        print()
    
    for step in range(0, total_steps, step_size):
        # Definir janelas de treino e teste
        train_end_idx = min_train_size + step
        test_idx = train_end_idx
        
        if test_idx >= len(concursos):
            break
            
        train_concursos = concursos[:train_end_idx]
        test_concurso = concursos[test_idx]
        
        # Filtrar dados de treino (apenas concursos passados)
        train_data = features_sorted.filter(
            pl.col('concurso').is_in(train_concursos)
        )
        
        # Filtrar dados de teste (concurso atual)
        test_data = features_sorted.filter(
            pl.col('concurso') == test_concurso
        )
        
        if len(test_data) == 0:
            continue
            
        # Formatar identificador do teste
        test_date_str = f"concurso_{test_concurso}"
        
        # Treinar modelo com dados históricos
        try:
            if use_gpu:
                model, scaler, weights = learn_weights_gpu(
                    train_data, 
                    use_gpu=True
                )
            else:
                model, scaler, weights = learn_weights_ridge(
                    train_data
                )
                
            # Calcular R² do modelo (se disponível)
            model_r2 = getattr(model, 'score', lambda x, y: 0.0)
            if callable(model_r2):
                try:
                    # Tentar calcular R² nos dados de treino
                    feature_cols = ['freq_total', 'roll10', 'roll25', 'last_seen', 'momentum5']
                    train_features = train_data.filter(pl.col('y_next').is_not_null())
                    if len(train_features) > 0:
                        X_train = train_features.select(feature_cols).to_numpy()
                        y_train = train_features.select('y_next').to_numpy().ravel()
                        if hasattr(scaler, 'transform'):
                            X_train_scaled = scaler.transform(X_train)
                            model_r2_value = model.score(X_train_scaled, y_train)
                        else:
                            model_r2_value = 0.0
                    else:
                        model_r2_value = 0.0
                except:
                    model_r2_value = 0.0
            else:
                model_r2_value = 0.0
                
        except Exception as e:
            if verbose:
                print(f"Erro no treino do passo {step + 1}: {e}")
            continue
        
        # Fazer predições no conjunto de teste
        try:
            # Filtrar apenas features do teste (sem y_next para evitar leakage)
            test_features = test_data.select([
                'concurso', 'n', 'tipo',
                'freq_total', 'roll10', 'roll25', 'last_seen', 'momentum5'
            ])
            
            if use_gpu:
                predictions = score_numbers_gpu(
                    test_features, 
                    weights, 
                    use_gpu=True
                )
            else:
                predictions = score_numbers(
                    test_features, 
                    weights
                )
                
        except Exception as e:
            if verbose:
                print(f"Erro na predição do passo {step + 1}: {e}")
            continue
        
        # Obter números reais sorteados (y_next do concurso anterior)
        # Buscar o próximo concurso para ver os números sorteados
        next_concurso_idx = test_idx + 1
        if next_concurso_idx < len(concursos):
            next_concurso = concursos[next_concurso_idx]
            actual_data = features_sorted.filter(
                (pl.col('concurso') == test_concurso) & 
                (pl.col('y_next') == 1)
            )
            actual_numbers = actual_data.select('n')['n'].to_list()
        else:
            # Último concurso - não temos y_next
            actual_numbers = []
        
        # Calcular métricas de acerto
        hits = 0
        top_5_hits = 0
        top_10_hits = 0
        
        if len(actual_numbers) > 0 and len(predictions) > 0:
            # Ordenar predições por score (maior primeiro)
            sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
            
            # Contar acertos
            for num in actual_numbers:
                if num in predictions:
                    hits += 1
            
            # Top 5 e Top 10
            top_5_nums = [num for num, _ in sorted_predictions[:5]]
            top_10_nums = [num for num, _ in sorted_predictions[:10]]
            
            top_5_hits = len(set(actual_numbers) & set(top_5_nums))
            top_10_hits = len(set(actual_numbers) & set(top_10_nums))
        
        # Calcular hit rate
        hit_rate = hits / len(actual_numbers) if len(actual_numbers) > 0 else 0.0
        
        # Armazenar resultado
        result = {
            'step': step + 1,
            'train_start': train_concursos[0],
            'train_end': train_concursos[-1],
            'test_concurso': test_concurso,
            'test_date': test_date_str,
            'train_size': len(train_concursos),
            'model_r2': model_r2_value,
            'predictions': predictions,
            'actual_numbers': actual_numbers,
            'hits': hits,
            'hit_rate': hit_rate,
            'top_5_hits': top_5_hits,
            'top_10_hits': top_10_hits,
            'weights_used': weights.copy()
        }
        
        results.append(result)
        
        if verbose:
            if len(actual_numbers) > 0:
                print(f"Passo {step + 1:3d}: Concurso {test_concurso} ({test_date_str}) - "
                      f"Treino: {len(train_concursos):3d} concursos - "
                      f"Acertos: {hits}/{len(actual_numbers)} ({hit_rate:.1%}) - "
                      f"Top5: {top_5_hits} - Top10: {top_10_hits} - "
                      f"R²: {model_r2_value:.3f}")
            else:
                print(f"Passo {step + 1:3d}: Concurso {test_concurso} ({test_date_str}) - "
                      f"Treino: {len(train_concursos):3d} concursos - "
                      f"Sem dados reais (último concurso) - "
                      f"R²: {model_r2_value:.3f}")
    
    if verbose:
        print(f"\nValidação concluída: {len(results)} passos executados")
        if len(results) > 0:
            avg_hits = np.mean([r['hits'] for r in results])
            avg_hit_rate = np.mean([r['hit_rate'] for r in results])
            avg_top5 = np.mean([r['top_5_hits'] for r in results])
            avg_top10 = np.mean([r['top_10_hits'] for r in results])
            print(f"Médias: {avg_hits:.2f} acertos ({avg_hit_rate:.1%}) - "
                  f"Top5: {avg_top5:.2f} - Top10: {avg_top10:.2f}")
    
    return results


def analyze_walkforward_results(results: List[Dict]) -> Dict:
    """
    Analisa os resultados da validação walk-forward.
    
    Args:
        results: Lista de resultados do walk_forward_validation
        
    Returns:
        Dict com estatísticas agregadas
    """
    if not results:
        return {}
    
    # Extrair métricas
    hits = [r['hits'] for r in results]
    hit_rates = [r['hit_rate'] for r in results]
    top_5_hits = [r['top_5_hits'] for r in results]
    top_10_hits = [r['top_10_hits'] for r in results]
    model_r2s = [r['model_r2'] for r in results]
    
    # Calcular estatísticas
    analysis = {
        'total_steps': len(results),
        'date_range': {
            'start': results[0]['test_date'],
            'end': results[-1]['test_date']
        },
        'hits': {
            'mean': np.mean(hits),
            'std': np.std(hits),
            'min': np.min(hits),
            'max': np.max(hits),
            'median': np.median(hits)
        },
        'hit_rate': {
            'mean': np.mean(hit_rates),
            'std': np.std(hit_rates),
            'min': np.min(hit_rates),
            'max': np.max(hit_rates),
            'median': np.median(hit_rates)
        },
        'top_5_hits': {
            'mean': np.mean(top_5_hits),
            'std': np.std(top_5_hits),
            'total': np.sum(top_5_hits)
        },
        'top_10_hits': {
            'mean': np.mean(top_10_hits),
            'std': np.std(top_10_hits),
            'total': np.sum(top_10_hits)
        },
        'model_performance': {
            'mean_r2': np.mean(model_r2s),
            'std_r2': np.std(model_r2s)
        },
        'consistency': {
            'steps_with_hits': sum(1 for h in hits if h > 0),
            'hit_consistency': sum(1 for h in hits if h > 0) / len(hits)
        }
    }
    
    return analysis


def run_walkforward_subset(
    features_df: pl.DataFrame,
    subset_size: int = 100,
    **kwargs
) -> Tuple[List[Dict], Dict]:
    """
    Executa walk-forward em um subset dos dados para teste rápido.
    
    Args:
        features_df: DataFrame com features
        subset_size: Quantos concursos usar (mais recentes)
        **kwargs: Argumentos para walk_forward_validation
        
    Returns:
        Tuple com (resultados, análise)
        
    Example:
        >>> results, analysis = run_walkforward_subset(features, subset_size=50)
        >>> print(f"Hit rate médio: {analysis['hit_rate']['mean']:.1%}")
    """
    # Pegar os concursos mais recentes
    recent_concursos = (
        features_df
        .select('concurso')
        .unique()
        .sort('concurso', descending=True)
        .head(subset_size)
        ['concurso'].to_list()
    )
    
    # Filtrar subset
    subset_df = features_df.filter(pl.col('concurso').is_in(recent_concursos))
    
    print(f"Executando walk-forward em subset de {len(recent_concursos)} concursos")
    
    # Executar validação
    results = walk_forward_validation(subset_df, **kwargs)
    
    # Analisar resultados
    analysis = analyze_walkforward_results(results)
    
    return results, analysis


if __name__ == "__main__":
    # Teste básico
    print("=== Teste do Módulo Walk-Forward ===")
    
    try:
        from src.etl.from_db import load_draws
        from src.features.make import build_number_features
        
        # Carregar dados
        print("Carregando dados...")
        df = load_draws("db/milionaria.db")
        features = build_number_features(df)
        
        # Teste em subset pequeno
        print("\nTestando em subset pequeno...")
        results, analysis = run_walkforward_subset(
            features, 
            subset_size=20,
            min_train_size=10,
            max_steps=5,
            verbose=True
        )
        
        print(f"\n=== Análise dos Resultados ===")
        print(f"Passos executados: {analysis['total_steps']}")
        print(f"Hit rate médio: {analysis['hit_rate']['mean']:.1%} ± {analysis['hit_rate']['std']:.1%}")
        print(f"Acertos médios: {analysis['hits']['mean']:.2f} ± {analysis['hits']['std']:.2f}")
        print(f"Consistência: {analysis['consistency']['hit_consistency']:.1%}")
        
    except ImportError as e:
        print(f"Módulos de dependência não encontrados: {e}")
        print("Execute este teste a partir do diretório raiz do projeto")
    except Exception as e:
        print(f"Erro no teste: {e}")