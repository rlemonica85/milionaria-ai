"""Script para validar integridade dos dados e detectar problemas."""

import sys
sys.path.append('src')

import polars as pl
from etl.from_db import load_draws
from features.make import latest_feature_snapshot, build_number_features
import os

def validate_database_integrity(db_path="db/milionaria.db"):
    """Valida a integridade completa do banco de dados."""
    print("=== Validação de Integridade dos Dados ===")
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # 1. Carregar dados
        print("1. Carregando dados...")
        df = load_draws(db_path)
        print(f"   ✓ {df.shape[0]} registros carregados")
        print(f"   ✓ Colunas: {df.columns}")
        
        # 2. Verificar estrutura básica
        print("\n2. Verificando estrutura básica...")
        required_cols = ['concurso', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"   ❌ Colunas obrigatórias ausentes: {missing_cols}")
            return False
        print("   ✓ Todas as colunas obrigatórias presentes")
        
        # 3. Verificar tipos de dados
        print("\n3. Verificando tipos de dados...")
        numeric_cols = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2']
        
        for col in numeric_cols:
            print(f"   Verificando coluna {col}...")
            
            # Verificar valores únicos
            unique_vals = df[col].unique().to_list()
            print(f"     - {len(unique_vals)} valores únicos")
            
            # Verificar se há valores problemáticos
            problematic_values = []
            for val in unique_vals[:20]:  # Verificar primeiros 20 valores
                if val is None:
                    continue
                    
                # Verificar se contém 'dezena'
                if isinstance(val, str) and 'dezena' in val:
                    problematic_values.append(f"'{val}' (contém 'dezena')")
                    continue
                
                # Verificar se é conversível para número
                try:
                    float(val)
                except (ValueError, TypeError):
                    if isinstance(val, str):
                        problematic_values.append(f"'{val}' (não numérico)")
                    else:
                        problematic_values.append(f"{val} (tipo: {type(val)})")
            
            if problematic_values:
                print(f"     ❌ Valores problemáticos encontrados: {problematic_values[:5]}")
                if len(problematic_values) > 5:
                    print(f"     ... e mais {len(problematic_values) - 5} valores")
                return False
            else:
                print(f"     ✓ Todos os valores são válidos")
        
        # 4. Verificar ranges válidos
        print("\n4. Verificando ranges válidos...")
        
        # Dezenas devem estar entre 1-50
        dezena_cols = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']
        for col in dezena_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            print(f"   {col}: {min_val} - {max_val}")
            
            if min_val < 1 or max_val > 50:
                print(f"     ❌ Range inválido para dezenas: {min_val}-{max_val}")
                return False
        
        # Trevos devem estar entre 1-6
        trevo_cols = ['T1', 'T2']
        for col in trevo_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            print(f"   {col}: {min_val} - {max_val}")
            
            if min_val < 1 or max_val > 6:
                print(f"     ❌ Range inválido para trevos: {min_val}-{max_val}")
                return False
        
        print("   ✓ Todos os ranges são válidos")
        
        # 5. Testar geração de features
        print("\n5. Testando geração de features...")
        try:
            features = build_number_features(df)
            print(f"   ✓ Features de treinamento geradas: {features.shape}")
            
            # Verificar se há 'dezena' nas features
            for col in features.columns:
                if col == 'tipo':  # Esta coluna deve conter 'dezena'
                    continue
                    
                sample_vals = features[col].head(10).to_list()
                for val in sample_vals:
                    if isinstance(val, str) and 'dezena' in val:
                        print(f"     ❌ Feature '{col}' contém 'dezena': {val}")
                        return False
            
            print("   ✓ Features de treinamento válidas")
            
        except Exception as feature_error:
            print(f"   ❌ Erro ao gerar features de treinamento: {feature_error}")
            return False
        
        # 6. Testar snapshot
        print("\n6. Testando snapshot...")
        try:
            snapshot = latest_feature_snapshot(df)
            print(f"   ✓ Snapshot gerado: {snapshot.shape}")
            
            # Verificar se há exatamente 50 dezenas e 6 trevos
            dezenas_count = len(snapshot.filter(pl.col('tipo') == 'dezena'))
            trevos_count = len(snapshot.filter(pl.col('tipo') == 'trevo'))
            
            print(f"   ✓ Dezenas no snapshot: {dezenas_count}")
            print(f"   ✓ Trevos no snapshot: {trevos_count}")
            
            if dezenas_count != 50:
                print(f"   ❌ Número incorreto de dezenas: {dezenas_count} (esperado: 50)")
                return False
                
            if trevos_count != 6:
                print(f"   ❌ Número incorreto de trevos: {trevos_count} (esperado: 6)")
                return False
            
            # Verificar se há 'dezena' em colunas numéricas
            numeric_feature_cols = ['freq_total', 'roll10', 'roll25', 'last_seen', 'momentum5']
            for col in numeric_feature_cols:
                if col in snapshot.columns:
                    sample_vals = snapshot[col].head(10).to_list()
                    for val in sample_vals:
                        if isinstance(val, str) and 'dezena' in val:
                            print(f"     ❌ Snapshot coluna '{col}' contém 'dezena': {val}")
                            return False
            
            print("   ✓ Snapshot válido")
            
        except Exception as snapshot_error:
            print(f"   ❌ Erro ao gerar snapshot: {snapshot_error}")
            return False
        
        # 7. Verificar dados recentes
        print("\n7. Verificando dados recentes...")
        if 'data' in df.columns:
            latest_date = df['data'].max()
            latest_concurso = df['concurso'].max()
            print(f"   ✓ Último concurso: {latest_concurso}")
            print(f"   ✓ Data mais recente: {latest_date}")
        
        print("\n=== ✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO ===\n")
        print("Resumo:")
        print(f"- {df.shape[0]} registros válidos")
        print(f"- {dezenas_count} dezenas no snapshot")
        print(f"- {trevos_count} trevos no snapshot")
        print(f"- Features de treinamento: {features.shape}")
        print("- Todos os dados estão íntegros")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE VALIDAÇÃO: {e}")
        if 'dezena' in str(e):
            print("🔍 ERRO RELACIONADO A 'DEZENA' DETECTADO!")
            print("Este é provavelmente o problema que está causando o erro no Streamlit.")
        
        import traceback
        traceback.print_exc()
        return False

def quick_data_check():
    """Verificação rápida dos dados para detectar problemas imediatos."""
    print("=== Verificação Rápida dos Dados ===")
    
    try:
        df = load_draws("db/milionaria.db")
        print(f"✓ Dados carregados: {df.shape}")
        
        # Verificar se há strings 'dezena' em colunas numéricas
        numeric_cols = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2']
        for col in numeric_cols:
            if col in df.columns:
                # Pegar uma amostra maior
                sample = df[col].head(50).to_list()
                dezena_found = [val for val in sample if isinstance(val, str) and 'dezena' in val]
                if dezena_found:
                    print(f"❌ PROBLEMA ENCONTRADO na coluna {col}: {dezena_found}")
                    return False
        
        print("✓ Verificação rápida passou - dados parecem íntegros")
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação rápida: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = quick_data_check()
    else:
        success = validate_database_integrity()
    
    if not success:
        print("\n🚨 PROBLEMAS DETECTADOS - Execute correções antes de usar o aplicativo")
        sys.exit(1)
    else:
        print("\n✅ DADOS VÁLIDOS - Aplicativo pode ser usado com segurança")
        sys.exit(0)