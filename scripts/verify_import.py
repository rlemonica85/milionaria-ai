#!/usr/bin/env python3
"""Script para verificar a importação dos dados no banco de dados."""

import sqlite3
from pathlib import Path

def verify_database():
    """Verifica o estado do banco de dados após importação."""
    db_path = "db/milionaria.db"
    
    if not Path(db_path).exists():
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabelas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tabelas encontradas: {[t[0] for t in tables]}")
        
        # Verificar estrutura da tabela sorteios
        cursor.execute("PRAGMA table_info(sorteios);")
        columns = cursor.fetchall()
        print(f"📊 Estrutura da tabela sorteios: {len(columns)} colunas")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM sorteios;")
        total = cursor.fetchone()[0]
        print(f"📈 Total de registros: {total}")
        
        # Verificar ranges de dados
        cursor.execute("""
            SELECT 
                MIN(d1), MAX(d1), MIN(d2), MAX(d2), MIN(d3), MAX(d3),
                MIN(d4), MAX(d4), MIN(d5), MAX(d5), MIN(d6), MAX(d6),
                MIN(t1), MAX(t1), MIN(t2), MAX(t2)
            FROM sorteios
        """)
        ranges = cursor.fetchone()
        print(f"🎯 Ranges das dezenas: D1[{ranges[0]}-{ranges[1]}], D2[{ranges[2]}-{ranges[3]}], D3[{ranges[4]}-{ranges[5]}]")
        print(f"   D4[{ranges[6]}-{ranges[7]}], D5[{ranges[8]}-{ranges[9]}], D6[{ranges[10]}-{ranges[11]}]")
        print(f"🍀 Ranges dos trevos: T1[{ranges[12]}-{ranges[13]}], T2[{ranges[14]}-{ranges[15]}]")
        
        # Verificar dados inválidos
        cursor.execute("""
            SELECT COUNT(*) FROM sorteios 
            WHERE d1 < 1 OR d1 > 50 OR d2 < 1 OR d2 > 50 OR d3 < 1 OR d3 > 50
               OR d4 < 1 OR d4 > 50 OR d5 < 1 OR d5 > 50 OR d6 < 1 OR d6 > 50
               OR t1 < 1 OR t1 > 6 OR t2 < 1 OR t2 > 6
        """)
        invalid = cursor.fetchone()[0]
        print(f"⚠️  Registros com dados inválidos: {invalid}")
        
        # Mostrar primeiros 5 registros
        cursor.execute("SELECT * FROM sorteios ORDER BY concurso LIMIT 5;")
        records = cursor.fetchall()
        print(f"\n📋 Primeiros 5 registros:")
        for record in records:
            print(f"   Concurso {record[0]}: {record[1]} | Dezenas: {record[2:8]} | Trevos: {record[8:10]}")
        
        conn.close()
        
        if invalid == 0 and total > 0:
            print(f"\n✅ Banco de dados válido: {total} registros sem problemas")
            return True
        else:
            print(f"\n❌ Problemas encontrados: {invalid} registros inválidos")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return False

if __name__ == "__main__":
    print("=== VERIFICAÇÃO DO BANCO DE DADOS ===")
    success = verify_database()
    exit(0 if success else 1)