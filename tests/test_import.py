#!/usr/bin/env python3
"""Script de teste para importação inicial usando dados de exemplo."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.db.schema import get_engine, ensure_schema
from src.db.io import upsert_rows, read_max_concurso, read_all_sorteios

def create_test_excel():
    """Cria um arquivo Excel de teste baseado no CSV de exemplo."""
    csv_path = "data/raw/exemplo_base_275.csv"
    excel_path = "data/raw/base_275.xlsx"
    
    if os.path.exists(csv_path):
        # Lê o CSV e salva como Excel
        df = pd.read_csv(csv_path)
        df.to_excel(excel_path, index=False)
        print(f"Arquivo Excel de teste criado: {excel_path}")
        return excel_path
    else:
        print(f"Arquivo CSV de exemplo não encontrado: {csv_path}")
        return None

def main():
    print("=== Teste de Importação Inicial ===\n")
    
    # 1. Cria arquivo Excel de teste
    excel_path = create_test_excel()
    if not excel_path:
        print("❌ Não foi possível criar arquivo de teste")
        return
    
    # 2. Prepara banco
    print("Preparando banco de dados...")
    engine = get_engine()
    ensure_schema(engine)
    
    # 3. Testa importação
    try:
        from src.ingest.import_initial import load_and_process_excel
        
        print(f"\nTestando importação de: {excel_path}")
        df = load_and_process_excel(excel_path)
        
        print(f"\nDados processados:")
        print(df.head())
        
        # 4. Importa para o banco
        print("\nImportando para o banco...")
        rows_affected = upsert_rows(df)
        
        # 5. Verifica resultado
        max_concurso = read_max_concurso()
        all_data = read_all_sorteios()
        
        print(f"\n✅ Teste concluído!")
        print(f"   - Linhas processadas: {len(df)}")
        print(f"   - Linhas no banco: {len(all_data)}")
        print(f"   - Máximo concurso: {max_concurso}")
        
        print(f"\nPrimeiros registros no banco:")
        print(all_data.head())
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()