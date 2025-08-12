"""Módulo de backtest paralelo usando multiprocessing para avaliação de bilhetes."""

import multiprocessing as mp
from typing import List, Tuple, Dict, Any
import polars as pl
from collections import defaultdict
from functools import partial


def evaluate_ticket_batch(batch_data: Tuple[List[Tuple[Tuple[int, ...], Tuple[int, int]]], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Avalia um batch de bilhetes contra histórico.
    
    Args:
        batch_data: Tupla com (tickets, historical_draws)
        
    Returns:
        Lista de resultados com métricas por bilhete
    """
    tickets, historical_draws = batch_data
    results = []
    
    for i, (dezenas, trevos) in enumerate(tickets):
        ticket_result = {
            'ticket_id': i,
            'dezenas': dezenas,
            'trevos': trevos,
            'total_hits_dezenas': 0,
            'total_hits_trevos': 0,
            'max_hits_dezenas': 0,
            'max_hits_trevos': 0,
            'hit_distribution_dezenas': defaultdict(int),
            'hit_distribution_trevos': defaultdict(int),
            'winning_draws': []
        }
        
        dezenas_set = set(dezenas)
        trevos_set = set(trevos)
        
        for draw in historical_draws:
            # Contar acertos nas dezenas
            draw_dezenas = set(draw['dezenas'])
            hits_dezenas = len(dezenas_set.intersection(draw_dezenas))
            
            # Contar acertos nos trevos
            draw_trevos = set(draw['trevos'])
            hits_trevos = len(trevos_set.intersection(draw_trevos))
            
            # Atualizar estatísticas
            ticket_result['total_hits_dezenas'] += hits_dezenas
            ticket_result['total_hits_trevos'] += hits_trevos
            ticket_result['max_hits_dezenas'] = max(ticket_result['max_hits_dezenas'], hits_dezenas)
            ticket_result['max_hits_trevos'] = max(ticket_result['max_hits_trevos'], hits_trevos)
            
            # Distribuição de acertos
            ticket_result['hit_distribution_dezenas'][hits_dezenas] += 1
            ticket_result['hit_distribution_trevos'][hits_trevos] += 1
            
            # Registrar sorteios com acertos significativos
            if hits_dezenas >= 3 or hits_trevos >= 1:
                ticket_result['winning_draws'].append({
                    'concurso': draw['concurso'],
                    'hits_dezenas': hits_dezenas,
                    'hits_trevos': hits_trevos,
                    'data': draw.get('data', 'N/A')
                })
        
        # Calcular métricas agregadas
        num_draws = len(historical_draws)
        ticket_result['avg_hits_dezenas'] = ticket_result['total_hits_dezenas'] / num_draws if num_draws > 0 else 0
        ticket_result['avg_hits_trevos'] = ticket_result['total_hits_trevos'] / num_draws if num_draws > 0 else 0
        ticket_result['score'] = calculate_score(ticket_result)
        
        results.append(ticket_result)
    
    return results


def calculate_score(result: Dict[str, Any]) -> float:
    """Calcula score composto para o bilhete.
    
    Args:
        result: Resultado do backtest
        
    Returns:
        Score normalizado (0-1)
    """
    # Peso para diferentes métricas
    weights = {
        'avg_hits_dezenas': 0.4,
        'avg_hits_trevos': 0.3,
        'max_hits_dezenas': 0.2,
        'max_hits_trevos': 0.1
    }
    
    # Normalizar métricas (assumindo máximos razoáveis)
    normalized_metrics = {
        'avg_hits_dezenas': min(result['avg_hits_dezenas'] / 3.0, 1.0),  # Max 3 acertos médios
        'avg_hits_trevos': min(result['avg_hits_trevos'] / 1.0, 1.0),    # Max 1 acerto médio
        'max_hits_dezenas': min(result['max_hits_dezenas'] / 6.0, 1.0),  # Max 6 acertos
        'max_hits_trevos': min(result['max_hits_trevos'] / 2.0, 1.0)     # Max 2 acertos
    }
    
    # Calcular score ponderado
    score = sum(weights[metric] * normalized_metrics[metric] for metric in weights)
    return score


def run_backtest_parallel(tickets: List[Tuple[Tuple[int, ...], Tuple[int, int]]], 
                         historical_data: pl.DataFrame,
                         num_workers: int = 4,
                         batch_size: int = 100) -> List[Dict[str, Any]]:
    """Executa backtest paralelo usando multiprocessing.
    
    Args:
        tickets: Lista de bilhetes para avaliar
        historical_data: DataFrame com dados históricos
        num_workers: Número de workers
        batch_size: Tamanho do batch por worker
        
    Returns:
        Lista de resultados ordenados por score
    """
    # Converter dados históricos para formato adequado
    historical_draws = []
    for row in historical_data.iter_rows(named=True):
        draw = {
            'concurso': row['concurso'],
            'dezenas': [row[f'D{i}'] for i in range(1, 7)],
            'trevos': [row['T1'], row['T2']],
            'data': row.get('data', 'N/A')
        }
        historical_draws.append(draw)
    
    # Dividir tickets em batches
    batches = [tickets[i:i + batch_size] for i in range(0, len(tickets), batch_size)]
    
    # Preparar dados para workers
    batch_data = [(batch, historical_draws) for batch in batches]
    
    # Executar em paralelo
    if num_workers > 1 and len(batches) > 1:
        with mp.Pool(processes=min(num_workers, len(batches))) as pool:
            batch_results = pool.map(evaluate_ticket_batch, batch_data)
    else:
        # Execução sequencial para casos simples
        batch_results = [evaluate_ticket_batch(data) for data in batch_data]
    
    # Coletar resultados
    all_results = []
    for batch_result in batch_results:
        all_results.extend(batch_result)
    
    # Reindexar ticket_ids
    for i, result in enumerate(all_results):
        result['ticket_id'] = i
    
    # Ordenar por score
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return all_results


def print_backtest_summary(results: List[Dict[str, Any]], top_k: int = 10):
    """Imprime resumo dos resultados do backtest.
    
    Args:
        results: Resultados do backtest
        top_k: Número de top bilhetes para mostrar
    """
    print(f"\n=== Resumo do Backtest (Top {top_k}) ===")
    print(f"Total de bilhetes avaliados: {len(results)}")
    
    if not results:
        print("Nenhum resultado encontrado.")
        return
    
    print(f"\n{'Rank':<4} {'Score':<8} {'Avg Dez':<8} {'Avg Trev':<9} {'Max Dez':<8} {'Max Trev':<9} {'Bilhete':<30}")
    print("-" * 90)
    
    for i, result in enumerate(results[:top_k]):
        rank = i + 1
        score = result['score']
        avg_dez = result['avg_hits_dezenas']
        avg_trev = result['avg_hits_trevos']
        max_dez = result['max_hits_dezenas']
        max_trev = result['max_hits_trevos']
        dezenas_str = str(result['dezenas'])
        trevos_str = str(result['trevos'])
        bilhete = f"{dezenas_str} + {trevos_str}"
        
        print(f"{rank:<4} {score:<8.4f} {avg_dez:<8.2f} {avg_trev:<9.2f} {max_dez:<8} {max_trev:<9} {bilhete:<30}")
    
    # Estatísticas gerais
    scores = [r['score'] for r in results]
    avg_scores = [r['avg_hits_dezenas'] for r in results]
    
    print(f"\n=== Estatísticas Gerais ===")
    print(f"Score médio: {sum(scores)/len(scores):.4f}")
    print(f"Melhor score: {max(scores):.4f}")
    print(f"Acertos médios (dezenas): {sum(avg_scores)/len(avg_scores):.2f}")
    print(f"Bilhetes com 4+ acertos máximos: {sum(1 for r in results if r['max_hits_dezenas'] >= 4)}")
    print(f"Bilhetes com 1+ trevo máximo: {sum(1 for r in results if r['max_hits_trevos'] >= 1)}")


if __name__ == "__main__":
    # Teste básico
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from src.etl.from_db import load_draws
    from src.features.make import build_number_features, latest_feature_snapshot
    from src.models.scoring import learn_weights_ridge, score_numbers
    from src.generate.tickets import generate_candidates, apply_filters, assign_trevos, load_filters_config
    
    print("=== Teste do Sistema de Backtest ===")
    
    # Carregar dados
    df = load_draws("db/milionaria.db")
    print(f"Dados carregados: {len(df)} sorteios")
    
    # Gerar alguns bilhetes para teste
    features = build_number_features(df)
    snapshot = latest_feature_snapshot(df)
    model, scaler, weights = learn_weights_ridge(features)
    scores = score_numbers(snapshot, weights)
    
    config = load_filters_config("configs/filters.yaml")
    tickets = generate_candidates(scores, k=6, top_pool=25, n=100, seed=42)
    filtered_tickets = apply_filters(tickets, config['filters'])
    complete_tickets = assign_trevos(filtered_tickets[:10], strategy='balanced', seed=42)
    
    print(f"Bilhetes para teste: {len(complete_tickets)}")
    
    # Executar backtest
    results = run_backtest_parallel(complete_tickets, df, num_workers=2, batch_size=5)
    
    # Mostrar resultados
    print_backtest_summary(results, top_k=5)
    
    print("\n=== Teste Finalizado ===")