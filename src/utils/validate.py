#!/usr/bin/env python3
"""Módulo para validação da integridade dos dados do banco de dados."""

import pandas as pd
from sqlalchemy import text
from src.db.schema import get_engine


class ValidationError(Exception):
    """Exceção customizada para erros de validação."""
    pass


def sanity_checks(db_path="db/milionaria.db"):
    """Verifica a integridade mínima dos dados no banco de dados.
    
    Args:
        db_path (str): Caminho para o arquivo do banco de dados
        
    Returns:
        bool: True se todos os checks passaram
        
    Raises:
        ValidationError: Se alguma regra de integridade for violada
    """
    engine = get_engine(db_path)
    
    with engine.connect() as conn:
        # Carrega todos os dados
        query = text("SELECT * FROM sorteios ORDER BY concurso")
        result = conn.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print("Banco vazio - nenhuma validacao necessaria")
            return True
        
        # Converte para DataFrame para facilitar validação
        columns = ['concurso', 'data', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 't1', 't2']
        df = pd.DataFrame(rows, columns=columns)
        
        print(f"Validando {len(df)} registros...")
        
        # Check 1: Data não nula
        _check_data_not_null(df)
        
        # Check 2: Dezenas no intervalo [1,50]
        _check_dezenas_range(df)
        
        # Check 3: Trevos no intervalo [1,6]
        _check_trevos_range(df)
        
        # Check 4: Concursos únicos
        _check_concursos_unicos(df)
        
        print("Todos os checks de integridade passaram!")
        return True


def _check_data_not_null(df):
    """Verifica se todas as datas são não nulas."""
    null_dates = df[df['data'].isnull()]
    if not null_dates.empty:
        concursos = null_dates['concurso'].tolist()
        raise ValidationError(f"Datas nulas encontradas nos concursos: {concursos}")
    print("Check 1/4: Todas as datas sao validas")


def _check_dezenas_range(df):
    """Verifica se todas as dezenas estão no intervalo [1,50]."""
    dezenas_cols = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6']
    
    for col in dezenas_cols:
        invalid_rows = df[(df[col] < 1) | (df[col] > 50)]
        if not invalid_rows.empty:
            concursos = invalid_rows['concurso'].tolist()
            valores = invalid_rows[col].tolist()
            raise ValidationError(
                f"Dezenas inválidas em {col}: concursos {concursos} com valores {valores}. "
                f"Esperado: [1,50]"
            )
    
    print("Check 2/4: Todas as dezenas estao no intervalo [1,50]")


def _check_trevos_range(df):
    """Verifica se todos os trevos estão no intervalo [1,6]."""
    trevos_cols = ['t1', 't2']
    
    for col in trevos_cols:
        invalid_rows = df[(df[col] < 1) | (df[col] > 6)]
        if not invalid_rows.empty:
            concursos = invalid_rows['concurso'].tolist()
            valores = invalid_rows[col].tolist()
            raise ValidationError(
                f"Trevos inválidos em {col}: concursos {concursos} com valores {valores}. "
                f"Esperado: [1,6]"
            )
    
    print("Check 3/4: Todos os trevos estao no intervalo [1,6]")


def _check_concursos_unicos(df):
    """Verifica se todos os concursos são únicos."""
    duplicados = df[df.duplicated(subset=['concurso'], keep=False)]
    if not duplicados.empty:
        concursos_dup = duplicados['concurso'].unique().tolist()
        raise ValidationError(f"Concursos duplicados encontrados: {concursos_dup}")
    
    print("Check 4/4: Todos os concursos sao unicos")


def main():
    """Função principal para execução direta do módulo."""
    try:
        print("Executando verificacoes de integridade do banco...")
        print("="*60)
        
        result = sanity_checks()
        
        print("\nResumo da validacao:")
        print(f"   • Status: {'APROVADO' if result else 'REPROVADO'}")
        print(f"   • Integridade: Garantida")
        print(f"   • Banco: Pronto para uso")
        
        return 0 if result else 1
        
    except ValidationError as e:
        print(f"\nERRO DE VALIDACAO: {e}")
        print("\nAcoes recomendadas:")
        print("   • Verificar dados de origem")
        print("   • Corrigir registros inválidos")
        print("   • Executar novamente a validação")
        return 1
        
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())