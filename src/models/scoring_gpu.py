"""Módulo para scoring de números da +Milionária usando GPU (cuML).

Este módulo implementa uma versão acelerada por GPU do sistema de scoring
usando cuML LinearRegression para aproveitar placas NVIDIA como RTX 3080.
"""

import numpy as np
import polars as pl
from typing import Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    import cuml
    from cuml.linear_model import LinearRegression as cuLinearRegression
    from cuml.preprocessing import StandardScaler as cuStandardScaler
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    # Fallback para CPU
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler


def learn_weights_gpu(
    history_feats: pl.DataFrame,
    alpha: float = 1e-6,  # Regularização mínima para LinearRegression
    random_state: int = 42,
    use_gpu: bool = True
) -> Tuple[object, object, Dict[str, float]]:
    """
    Aprende pesos das features usando GPU-accelerated LinearRegression (cuML).
    
    Args:
        history_feats: DataFrame com features históricas incluindo y_next
        alpha: Parâmetro de regularização (mínimo para LinearRegression)
        random_state: Seed para reprodutibilidade
        use_gpu: Se True, usa cuML (GPU). Se False ou GPU indisponível, usa sklearn
        
    Returns:
        Tuple contendo:
        - modelo LinearRegression treinado (cuML ou sklearn)
        - scaler para normalização (cuML ou sklearn)
        - pesos default como fallback
        
    Example:
        >>> from src.etl.from_db import load_draws
        >>> from src.features.make import build_number_features
        >>> df = load_draws("db/milionaria.db")
        >>> features = build_number_features(df)
        >>> model, scaler, defaults = learn_weights_gpu(features)
    """
    # Pesos default como fallback
    default_weights = {
        'freq_total': 0.3,
        'roll10': 0.25,
        'roll25': 0.2,
        'last_seen': -0.15,  # Sinal invertido: quanto maior, menor o score
        'momentum5': 0.2
    }
    
    # Verificar disponibilidade da GPU
    use_gpu_actual = use_gpu and GPU_AVAILABLE
    
    if use_gpu and not GPU_AVAILABLE:
        print("Aviso: cuML não disponível, usando CPU (sklearn)")
    
    # Preparar dados para treinamento
    feature_cols = ['freq_total', 'roll10', 'roll25', 'last_seen', 'momentum5']
    
    # Filtrar apenas dados com y_next válido
    train_data = history_feats.filter(pl.col('y_next').is_not_null())
    
    if len(train_data) == 0:
        print("Aviso: Nenhum dado de treino disponível, usando pesos default")
        # Retorna modelo dummy
        if use_gpu_actual:
            model = cuLinearRegression()
            scaler = cuStandardScaler()
        else:
            model = LinearRegression()
            scaler = StandardScaler()
        return model, scaler, default_weights
    
    # Extrair features e target
    X = train_data.select(feature_cols).to_numpy().astype(np.float32)
    y = train_data.select('y_next').to_numpy().ravel().astype(np.float32)
    
    if use_gpu_actual:
        print(f"Usando GPU (cuML) para treinamento com {len(train_data)} amostras")
        
        # Converter para GPU arrays
        X_gpu = cp.asarray(X)
        y_gpu = cp.asarray(y)
        
        # Normalizar features na GPU
        scaler = cuStandardScaler()
        X_scaled = scaler.fit_transform(X_gpu)
        
        # Treinar modelo LinearRegression na GPU
        model = cuLinearRegression()
        model.fit(X_scaled, y_gpu)
        
        # Obter coeficientes (converter de GPU para CPU)
        coef_gpu = model.coef_
        if hasattr(coef_gpu, 'get'):
            coef_cpu = coef_gpu.get()  # CuPy array para NumPy
        else:
            coef_cpu = np.array(coef_gpu)  # Já é NumPy
            
        # Calcular R² score
        y_pred = model.predict(X_scaled)
        if hasattr(y_pred, 'get'):
            y_pred_cpu = y_pred.get()
        else:
            y_pred_cpu = np.array(y_pred)
            
        if hasattr(y_gpu, 'get'):
            y_cpu = y_gpu.get()
        else:
            y_cpu = np.array(y_gpu)
            
        # Calcular R² manualmente
        ss_res = np.sum((y_cpu - y_pred_cpu) ** 2)
        ss_tot = np.sum((y_cpu - np.mean(y_cpu)) ** 2)
        r2_score = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
    else:
        print(f"Usando CPU (sklearn) para treinamento com {len(train_data)} amostras")
        
        # Normalizar features na CPU
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Treinar modelo LinearRegression na CPU
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        coef_cpu = model.coef_
        r2_score = model.score(X_scaled, y)
    
    # Blend com pesos default (70% modelo, 30% default)
    learned_weights = dict(zip(feature_cols, coef_cpu))
    blended_weights = {}
    
    for feature in feature_cols:
        learned_w = learned_weights.get(feature, 0.0)
        default_w = default_weights.get(feature, 0.0)
        blended_weights[feature] = 0.7 * learned_w + 0.3 * default_w
    
    device_type = "GPU (cuML)" if use_gpu_actual else "CPU (sklearn)"
    print(f"Modelo treinado em {device_type}")
    print(f"Score R² do modelo: {r2_score:.4f}")
    
    return model, scaler, blended_weights


def score_numbers_gpu(
    snapshot: pl.DataFrame,
    weights: Dict[str, float],
    normalize: bool = True,
    use_gpu: bool = True
) -> Dict[int, float]:
    """
    Calcula scores para cada número baseado nas features e pesos (versão GPU).
    
    Args:
        snapshot: DataFrame com features do último sorteio (sem y_next)
        weights: Dicionário com pesos para cada feature
        normalize: Se True, normaliza scores para [0, 1]
        use_gpu: Se True, usa operações GPU quando possível
        
    Returns:
        Dict mapeando número -> score
         
     Example:
         >>> from src.features.make import latest_feature_snapshot
         >>> snapshot = latest_feature_snapshot(df)
         >>> weights = {'freq_total': 0.3, 'roll10': 0.25, ...}
         >>> scores = score_numbers_gpu(snapshot, weights)
    """
    use_gpu_actual = use_gpu and GPU_AVAILABLE
    
    # Filtrar apenas dezenas (1-50)
    dezenas = snapshot.filter(pl.col('tipo') == 'dezena')
    
    if len(dezenas) != 50:
        raise ValueError(f"Esperado 50 dezenas, encontrado {len(dezenas)}")
    
    # Calcular scores
    feature_cols = ['freq_total', 'roll10', 'roll25', 'last_seen', 'momentum5']
    
    if use_gpu_actual:
        # Usar GPU para cálculos
        features_array = dezenas.select(feature_cols).to_numpy().astype(np.float32)
        features_gpu = cp.asarray(features_array)
        
        # Aplicar pesos na GPU
        scores_gpu = cp.zeros(len(dezenas), dtype=cp.float32)
        
        for i, feature in enumerate(feature_cols):
            weight = weights.get(feature, 0.0)
            scores_gpu += features_gpu[:, i] * weight
        
        # Converter de volta para CPU
        scores = scores_gpu.get()
        
    else:
        # Usar CPU para cálculos
        scores = np.zeros(len(dezenas))
        
        for feature in feature_cols:
            weight = weights.get(feature, 0.0)
            feature_values = dezenas.select(feature).to_numpy().ravel()
            scores += feature_values * weight
    
    # Normalizar scores se solicitado
    if normalize and len(scores) > 0:
        min_score = np.min(scores)
        max_score = np.max(scores)
        if max_score > min_score:
            scores = (scores - min_score) / (max_score - min_score)
        else:
            # Todos os scores são iguais - definir como 0.5
            scores = np.full_like(scores, 0.5)
    
    # Mapear números para scores
    numeros = dezenas.select('n').to_numpy().ravel()
    score_dict = dict(zip(numeros, scores))
    
    device_type = "GPU" if use_gpu_actual else "CPU"
    print(f"Scores calculados em {device_type} para {len(score_dict)} números")
    
    return score_dict


def get_gpu_info() -> Dict[str, any]:
    """
    Retorna informações sobre disponibilidade e status da GPU.
    
    Returns:
        Dict com informações da GPU
    """
    info = {
        'cuml_available': GPU_AVAILABLE,
        'gpu_count': 0,
        'gpu_memory': [],
        'cuda_version': None
    }
    
    if GPU_AVAILABLE:
        try:
            import cupy as cp
            info['gpu_count'] = cp.cuda.runtime.getDeviceCount()
            info['cuda_version'] = cp.cuda.runtime.runtimeGetVersion()
            
            # Informações de memória para cada GPU
            for i in range(info['gpu_count']):
                with cp.cuda.Device(i):
                    meminfo = cp.cuda.runtime.memGetInfo()
                    free_mem = meminfo[0] / (1024**3)  # GB
                    total_mem = meminfo[1] / (1024**3)  # GB
                    info['gpu_memory'].append({
                        'device': i,
                        'free_gb': round(free_mem, 2),
                        'total_gb': round(total_mem, 2),
                        'used_gb': round(total_mem - free_mem, 2)
                    })
                    
        except Exception as e:
            info['error'] = str(e)
    
    return info


# Instruções para troca no pipeline
def get_pipeline_instructions() -> str:
    """
    Retorna instruções para trocar do scoring CPU para GPU no pipeline.
    
    Returns:
        String com instruções de uso
    """
    return """
    INSTRUÇÕES PARA ATIVAR MODO GPU:
    
    1. Substituir imports:
       # De:
       from src.models.scoring import learn_weights_ridge, score_numbers
       
       # Para:
       from src.models.scoring_gpu import learn_weights_gpu, score_numbers_gpu
    
    2. Substituir chamadas de função:
       # De:
       model, scaler, weights = learn_weights_ridge(features)
       scores = score_numbers(snapshot, weights)
       
       # Para:
       model, scaler, weights = learn_weights_gpu(features, use_gpu=True)
       scores = score_numbers_gpu(snapshot, weights, use_gpu=True)
    
    3. Verificar status da GPU:
       from src.models.scoring_gpu import get_gpu_info
       gpu_info = get_gpu_info()
       print(gpu_info)
    
    4. Fallback automático:
       - Se cuML não estiver disponível, usa sklearn automaticamente
       - Se use_gpu=False, força uso de CPU
       - Compatibilidade total com pipeline existente
    
    REQUISITOS:
    - NVIDIA GPU (RTX 3080 recomendada)
    - CUDA 11.2+
    - cuML instalado: conda install -c rapidsai cuml
    """


if __name__ == "__main__":
    # Teste básico
    print("=== Teste do Módulo GPU ===")
    
    # Verificar GPU
    gpu_info = get_gpu_info()
    print(f"GPU disponível: {gpu_info['cuml_available']}")
    if gpu_info['cuml_available']:
        print(f"GPUs encontradas: {gpu_info['gpu_count']}")
        for mem in gpu_info['gpu_memory']:
            print(f"  GPU {mem['device']}: {mem['free_gb']:.1f}GB livre / {mem['total_gb']:.1f}GB total")
    
    # Mostrar instruções
    print("\n" + get_pipeline_instructions())