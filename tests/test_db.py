#!/usr/bin/env python3
"""Script de teste para criar e verificar o banco de dados."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.db.schema import get_engine, ensure_schema
from src.db.io import upsert_rows, read_max_concurso, read_all_sorteios

def main():
    print("=== Teste do Banco de Dados Milionária ===\n")
    
    # 1. Criar engine e schema
    print("1. Criando banco de dados e tabela...")
    engine = get_engine()
    ensure_schema(engine)
    
    # 2. Inserir dados de teste
    print("\n2. Inserindo dados de teste...")
    test_data = pd.DataFrame({
        'concurso': [1, 2, 3],
        'data': ['2023-01-01', '2023-01-08', '2023-01-15'],
        'd1': [1, 5, 10], 'd2': [2, 10, 15], 'd3': [3, 15, 20], 
        'd4': [4, 20, 25], 'd5': [5, 25, 30], 'd6': [6, 30, 35],
        't1': [1, 2, 3], 't2': [2, 3, 4]
    })
    
    upsert_rows(test_data)
    
    # 3. Verificar máximo concurso
    print("\n3. Verificando máximo concurso...")
    max_concurso = read_max_concurso()
    print(f"Máximo concurso: {max_concurso}")
    
    # 4. Listar todos os sorteios
    print("\n4. Listando todos os sorteios:")
    df_sorteios = read_all_sorteios()
    print(df_sorteios)
    
    # 5. Teste de idempotência (inserir novamente)
    print("\n5. Testando idempotência (inserir dados duplicados)...")
    upsert_rows(test_data)  # Deve não duplicar
    
    df_final = read_all_sorteios()
    print(f"Total de registros após upsert duplicado: {len(df_final)}")
    
    print("\n✅ Teste concluído com sucesso!")

if __name__ == "__main__":
    main()