#!/usr/bin/env python3
"""Script para coletar estatísticas do banco de dados."""

import sys
sys.path.append('.')

from src.db.io import read_max_concurso, read_all_sorteios

def main():
    try:
        df = read_all_sorteios()
        max_concurso = read_max_concurso()
        print(f"Total de registros: {len(df)}")
        print(f"Ultimo concurso: {max_concurso}")
        return 0
    except Exception as e:
        print(f"Erro ao coletar estatísticas: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())