#!/usr/bin/env python3
"""Módulo para importação inicial da planilha histórica da +Milionária."""

import pandas as pd
from datetime import datetime
import os
import sys

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.db.schema import get_engine, ensure_schema
from src.db.io import upsert_rows


def normalize_column_names(df):
    """Normaliza nomes das colunas para o padrão esperado.
    
    Args:
        df (pandas.DataFrame): DataFrame com colunas originais
        
    Returns:
        pandas.DataFrame: DataFrame com colunas normalizadas
    """
    # Mapeamento de possíveis nomes de colunas
    column_mapping = {
        'Concurso': 'concurso',
        'concurso': 'concurso',
        'CONCURSO': 'concurso',
        'Data': 'data',
        'data': 'data',
        'DATA': 'data',
        'Data Sorteio': 'data',
        'D1': 'd1', 'D2': 'd2', 'D3': 'd3', 'D4': 'd4', 'D5': 'd5', 'D6': 'd6',
        'd1': 'd1', 'd2': 'd2', 'd3': 'd3', 'd4': 'd4', 'd5': 'd5', 'd6': 'd6',
        'T1': 't1', 'T2': 't2',
        't1': 't1', 't2': 't2',
        'Trevo 1': 't1', 'Trevo 2': 't2'
    }
    
    # Renomeia as colunas
    df_normalized = df.rename(columns=column_mapping)
    
    return df_normalized


def parse_dates(df, date_column='data'):
    """Converte coluna de data do formato DD/MM/AAAA para datetime.
    
    Args:
        df (pandas.DataFrame): DataFrame com coluna de data
        date_column (str): Nome da coluna de data
        
    Returns:
        pandas.DataFrame: DataFrame com datas convertidas
    """
    df = df.copy()
    
    # Tenta diferentes formatos de data
    date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y']
    
    for date_format in date_formats:
        try:
            df[date_column] = pd.to_datetime(df[date_column], format=date_format)
            print(f"Datas convertidas usando formato: {date_format}")
            break
        except (ValueError, TypeError):
            continue
    else:
        # Se nenhum formato funcionou, tenta conversão automática
        try:
            df[date_column] = pd.to_datetime(df[date_column], dayfirst=True)
            print("Datas convertidas usando detecção automática")
        except Exception as e:
            raise ValueError(f"Não foi possível converter as datas: {e}")
    
    return df


def cast_to_int(df, int_columns):
    """Converte colunas especificadas para int.
    
    Args:
        df (pandas.DataFrame): DataFrame original
        int_columns (list): Lista de colunas para converter
        
    Returns:
        pandas.DataFrame: DataFrame com colunas convertidas
    """
    df = df.copy()
    
    for col in int_columns:
        if col in df.columns:
            try:
                # Remove valores NaN e converte para int
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            except Exception as e:
                print(f"Aviso: Erro ao converter coluna {col} para int: {e}")
                # Mantém como está se não conseguir converter
    
    return df


def load_and_process_excel(file_path):
    """Carrega e processa a planilha Excel.
    
    Args:
        file_path (str): Caminho para o arquivo Excel
        
    Returns:
        pandas.DataFrame: DataFrame processado
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    print(f"Carregando planilha: {file_path}")
    
    # Carrega a planilha
    try:
        df = pd.read_excel(file_path)
        print(f"Planilha carregada: {len(df)} linhas, {len(df.columns)} colunas")
        print(f"Colunas originais: {list(df.columns)}")
    except Exception as e:
        raise ValueError(f"Erro ao carregar planilha: {e}")
    
    # Normaliza nomes das colunas
    df = normalize_column_names(df)
    print(f"Colunas normalizadas: {list(df.columns)}")
    
    # Verifica se todas as colunas necessárias estão presentes
    required_cols = ['concurso', 'data', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 't1', 't2']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
    
    # Processa datas
    df = parse_dates(df, 'data')
    
    # Converte colunas numéricas para int
    int_columns = ['concurso', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 't1', 't2']
    df = cast_to_int(df, int_columns)
    
    # Remove linhas com dados inválidos
    df = df.dropna(subset=required_cols)
    
    print(f"Dados processados: {len(df)} linhas válidas")
    return df[required_cols]


def main():
    """Função principal para importação inicial."""
    print("=== Importação Inicial da +Milionária ===\n")
    
    # Caminho para a planilha
    excel_path = "data/raw/base_275.xlsx"
    
    try:
        # 1. Carrega e processa a planilha
        df = load_and_process_excel(excel_path)
        
        # 2. Garante que o banco e schema existem
        print("\nPreparando banco de dados...")
        engine = get_engine()
        ensure_schema(engine)
        
        # 3. Importa os dados
        print("\nImportando dados para o banco...")
        rows_affected = upsert_rows(df)
        
        # 4. Verifica o resultado
        from src.db.io import read_max_concurso
        max_concurso = read_max_concurso()
        
        print(f"\n✅ Importação concluída!")
        print(f"   - Linhas processadas: {len(df)}")
        print(f"   - Linhas afetadas no banco: {rows_affected}")
        print(f"   - Máximo concurso: {max_concurso}")
        
        # Verifica se atingiu o critério mínimo
        if max_concurso >= 275:
            print(f"   - ✅ Critério atendido: COUNT(*) >= 275")
        else:
            print(f"   - ⚠️  Critério não atendido: COUNT(*) < 275")
            
    except Exception as e:
        print(f"❌ Erro durante a importação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()