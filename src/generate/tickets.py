"""Módulo para geração de tickets da +Milionária baseados em scores.

Este módulo gera combinações plausíveis de números usando scores calculados
pelo módulo de scoring, aplicando filtros estatísticos e estratégias para trevos.
"""

import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from itertools import combinations
import yaml
from pathlib import Path


def generate_candidates(
    score_map: Dict[int, float],
    k: int = 6,
    top_pool: int = 25,
    n: int = 4000,
    seed: Optional[int] = 42
) -> List[Tuple[int, ...]]:
    """
    Gera candidatos de tickets baseados nos scores dos números.
    
    Args:
        score_map: Dicionário {numero: score} para dezenas 1-50
        k: Quantidade de números por ticket (padrão: 6)
        top_pool: Tamanho do pool dos números com maiores scores
        n: Quantidade de tickets a gerar
        seed: Seed para reprodutibilidade
        
    Returns:
        Lista de tuplas com combinações de k números
        
    Example:
        >>> scores = {1: 0.8, 2: 0.6, 3: 0.9, 4: 0.4, 5: 0.7}
        >>> tickets = generate_candidates(scores, k=3, top_pool=4, n=10)
        >>> len(tickets) <= 10
        True
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Validar entrada
    if len(score_map) != 50:
        raise ValueError(f"score_map deve conter 50 números, encontrado {len(score_map)}")
    
    if not all(1 <= num <= 50 for num in score_map.keys()):
        raise ValueError("score_map deve conter números de 1 a 50")
    
    if k > top_pool:
        raise ValueError(f"k ({k}) não pode ser maior que top_pool ({top_pool})")
    
    # Ordenar números por score (maior para menor)
    sorted_numbers = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
    
    # Criar pool dos top números
    top_numbers = [num for num, _ in sorted_numbers[:top_pool]]
    
    # Criar pesos baseados nos scores (normalizar para probabilidades)
    top_scores = [score for _, score in sorted_numbers[:top_pool]]
    
    # Evitar divisão por zero
    if sum(top_scores) == 0:
        weights = [1.0] * len(top_numbers)
    else:
        weights = [score / sum(top_scores) for score in top_scores]
    
    # Gerar combinações
    tickets = set()  # Usar set para evitar duplicatas
    max_attempts = n * 10  # Limite de tentativas para evitar loop infinito
    attempts = 0
    
    while len(tickets) < n and attempts < max_attempts:
        # Selecionar k números com base nos pesos
        selected = np.random.choice(
            top_numbers, 
            size=k, 
            replace=False, 
            p=weights
        )
        
        # Ordenar e adicionar como tupla
        ticket = tuple(sorted(selected))
        tickets.add(ticket)
        attempts += 1
    
    # Converter para lista
    result = list(tickets)
    
    # Se não conseguiu gerar n tickets únicos, gerar combinações determinísticas
    if len(result) < n:
        # Gerar todas as combinações possíveis do pool
        all_combinations = list(combinations(top_numbers, k))
        
        # Embaralhar e pegar até n
        random.shuffle(all_combinations)
        result = all_combinations[:n]
    
    return result[:n]


def apply_filters(
    tickets: List[Tuple[int, ...]],
    filters_dict: Dict[str, any]
) -> List[Tuple[int, ...]]:
    """
    Aplica filtros estatísticos aos tickets.
    
    Args:
        tickets: Lista de tickets (tuplas de números)
        filters_dict: Dicionário com filtros a aplicar
            - min_sum: Soma mínima dos números
            - max_sum: Soma máxima dos números
            - min_even: Quantidade mínima de números pares
            - max_even: Quantidade máxima de números pares
            - max_spread: Spread máximo (max - min)
            
    Returns:
        Lista de tickets que passaram nos filtros
        
    Example:
        >>> tickets = [(1, 2, 3, 4, 5, 6), (10, 20, 30, 40, 45, 50)]
        >>> filters = {'min_sum': 50, 'max_sum': 200, 'min_even': 2, 'max_even': 4}
        >>> filtered = apply_filters(tickets, filters)
        >>> len(filtered) <= len(tickets)
        True
    """
    filtered_tickets = []
    
    for ticket in tickets:
        # Calcular estatísticas do ticket
        ticket_sum = sum(ticket)
        even_count = sum(1 for num in ticket if num % 2 == 0)
        spread = max(ticket) - min(ticket)
        
        # Aplicar filtros
        passes_filters = True
        
        # Filtro de soma mínima
        if 'min_sum' in filters_dict:
            if ticket_sum < filters_dict['min_sum']:
                passes_filters = False
        
        # Filtro de soma máxima
        if 'max_sum' in filters_dict:
            if ticket_sum > filters_dict['max_sum']:
                passes_filters = False
        
        # Filtro de números pares mínimos
        if 'min_even' in filters_dict:
            if even_count < filters_dict['min_even']:
                passes_filters = False
        
        # Filtro de números pares máximos
        if 'max_even' in filters_dict:
            if even_count > filters_dict['max_even']:
                passes_filters = False
        
        # Filtro de spread máximo
        if 'max_spread' in filters_dict:
            if spread > filters_dict['max_spread']:
                passes_filters = False
        
        if passes_filters:
            filtered_tickets.append(ticket)
    
    return filtered_tickets


def assign_trevos(
    tickets: List[Tuple[int, ...]],
    strategy: str = "balanced",
    seed: Optional[int] = 42
) -> List[Tuple[Tuple[int, ...], Tuple[int, int]]]:
    """
    Atribui trevos aos tickets usando diferentes estratégias.
    
    Args:
        tickets: Lista de tickets (tuplas de dezenas)
        strategy: Estratégia para atribuir trevos
            - "balanced": Distribui trevos de forma equilibrada
            - "random": Atribui trevos aleatoriamente
            - "low": Prefere trevos baixos (1, 2, 3)
            - "high": Prefere trevos altos (4, 5, 6)
        seed: Seed para reprodutibilidade
        
    Returns:
        Lista de tuplas (dezenas, (trevo1, trevo2))
        
    Example:
        >>> tickets = [(1, 2, 3, 4, 5, 6), (10, 20, 30, 40, 45, 50)]
        >>> complete = assign_trevos(tickets, strategy="balanced")
        >>> len(complete) == len(tickets)
        True
        >>> all(1 <= t1 <= 6 and 1 <= t2 <= 6 for _, (t1, t2) in complete)
        True
    """
    if seed is not None:
        random.seed(seed)
    
    complete_tickets = []
    
    for i, ticket in enumerate(tickets):
        if strategy == "balanced":
            # Distribui trevos de forma equilibrada
            trevo1 = (i % 6) + 1
            trevo2 = ((i + 3) % 6) + 1
            if trevo1 == trevo2:
                trevo2 = (trevo2 % 6) + 1
        
        elif strategy == "random":
            # Trevos completamente aleatórios
            trevos = random.sample(range(1, 7), 2)
            trevo1, trevo2 = sorted(trevos)
        
        elif strategy == "low":
            # Prefere trevos baixos
            trevos = random.choices(range(1, 4), k=2)
            while trevos[0] == trevos[1]:
                trevos = random.choices(range(1, 4), k=2)
            trevo1, trevo2 = sorted(trevos)
        
        elif strategy == "high":
            # Prefere trevos altos
            trevos = random.choices(range(4, 7), k=2)
            while trevos[0] == trevos[1]:
                trevos = random.choices(range(4, 7), k=2)
            trevo1, trevo2 = sorted(trevos)
        
        else:
            raise ValueError(f"Estratégia '{strategy}' não reconhecida")
        
        complete_tickets.append((ticket, (trevo1, trevo2)))
    
    return complete_tickets


def load_filters_config(config_path: str = "configs/filters.yaml") -> Dict:
    """
    Carrega configuração de filtros do arquivo YAML.
    
    Args:
        config_path: Caminho para o arquivo de configuração
        
    Returns:
        Dicionário com configurações de filtros
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Arquivo {config_path} não encontrado, usando configuração padrão")
        return get_default_config()
    except Exception as e:
        print(f"Erro ao carregar {config_path}: {e}, usando configuração padrão")
        return get_default_config()


def get_default_config() -> Dict:
    """
    Retorna configuração padrão de filtros.
    
    Returns:
        Dicionário com configuração padrão
    """
    return {
        'generation': {
            'k': 6,
            'top_pool': 25,
            'n': 4000,
            'seed': 42
        },
        'filters': {
            'min_sum': 60,
            'max_sum': 240,
            'min_even': 2,
            'max_even': 4,
            'max_spread': 45
        },
        'trevos': {
            'strategy': 'balanced',
            'seed': 42
        },
        'output': {
            'top_k': 50
        }
    }


if __name__ == "__main__":
    # Teste do módulo
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from src.etl.from_db import load_draws
    from src.features.make import build_number_features, latest_feature_snapshot
    from src.models.scoring import learn_weights_ridge, score_numbers
    
    print("=== Teste do Módulo de Geração de Tickets ===")
    
    # Carregar dados e calcular scores
    df = load_draws("db/milionaria.db")
    features = build_number_features(df)
    snapshot = latest_feature_snapshot(df)
    model, scaler, weights = learn_weights_ridge(features)
    scores = score_numbers(snapshot, weights)
    
    print(f"Scores calculados para {len(scores)} números")
    
    # Gerar candidatos
    print("\n=== Gerando Candidatos ===")
    config = get_default_config()
    
    tickets = generate_candidates(
        scores,
        k=config['generation']['k'],
        top_pool=config['generation']['top_pool'],
        n=config['generation']['n'],
        seed=config['generation']['seed']
    )
    
    print(f"Candidatos gerados: {len(tickets)}")
    print(f"Tickets únicos: {len(set(tickets))}")
    print(f"Exemplo: {tickets[0]}")
    
    # Aplicar filtros
    print("\n=== Aplicando Filtros ===")
    filtered_tickets = apply_filters(tickets, config['filters'])
    
    print(f"Tickets antes dos filtros: {len(tickets)}")
    print(f"Tickets após filtros: {len(filtered_tickets)}")
    print(f"Taxa de aprovação: {len(filtered_tickets)/len(tickets)*100:.1f}%")
    
    # Validar filtros
    if filtered_tickets:
        sums = [sum(ticket) for ticket in filtered_tickets]
        evens = [sum(1 for num in ticket if num % 2 == 0) for ticket in filtered_tickets]
        
        print(f"\nValidação dos filtros:")
        print(f"  Somas: {min(sums)} - {max(sums)} (esperado: {config['filters']['min_sum']} - {config['filters']['max_sum']})")
        print(f"  Pares: {min(evens)} - {max(evens)} (esperado: {config['filters']['min_even']} - {config['filters']['max_even']})")
    
    # Atribuir trevos
    print("\n=== Atribuindo Trevos ===")
    top_tickets = filtered_tickets[:config['output']['top_k']]
    complete_tickets = assign_trevos(
        top_tickets,
        strategy=config['trevos']['strategy'],
        seed=config['trevos']['seed']
    )
    
    print(f"Tickets completos: {len(complete_tickets)}")
    print(f"Exemplo completo: {complete_tickets[0]}")
    
    # Verificar trevos
    trevos_used = []
    for _, (t1, t2) in complete_tickets:
        trevos_used.extend([t1, t2])
    
    from collections import Counter
    trevo_counts = Counter(trevos_used)
    print(f"\nDistribuição de trevos: {dict(trevo_counts)}")
    
    print("\n=== Verificações Finais ===")
    print(f"✓ Sem duplicatas: {len(tickets) == len(set(tickets))}")
    print(f"✓ Filtros aplicados: {len(filtered_tickets) <= len(tickets)}")
    print(f"✓ Trevos válidos: {all(1 <= t1 <= 6 and 1 <= t2 <= 6 for _, (t1, t2) in complete_tickets)}")
    print(f"✓ Range de somas válido: {all(config['filters']['min_sum'] <= sum(ticket) <= config['filters']['max_sum'] for ticket in filtered_tickets)}")
    print(f"✓ Range de pares válido: {all(config['filters']['min_even'] <= sum(1 for num in ticket if num % 2 == 0) <= config['filters']['max_even'] for ticket in filtered_tickets)}")