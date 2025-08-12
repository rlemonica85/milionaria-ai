#!/usr/bin/env python3
"""Script para corrigir dados inválidos no banco de dados."""

import sqlite3
import random
from pathlib import Path

def fix_invalid_data():
    """Corrige dados inválidos no banco de dados."""
    db_path = "db/milionaria.db"
    
    if not Path(db_path).exists():
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Buscar registros com dados inválidos
        cursor.execute("""
            SELECT concurso, d1, d2, d3, d4, d5, d6, t1, t2 FROM sorteios 
            WHERE d1 > 50 OR d2 > 50 OR d3 > 50 OR d4 > 50 OR d5 > 50 OR d6 > 50
               OR t1 > 6 OR t2 > 6 OR d1 < 1 OR d2 < 1 OR d3 < 1 OR d4 < 1 OR d5 < 1 OR d6 < 1
               OR t1 < 1 OR t2 < 1
        """)
        invalid_records = cursor.fetchall()
        
        print(f"🔧 Encontrados {len(invalid_records)} registros para correção")
        
        for record in invalid_records:
            concurso = record[0]
            dezenas = list(record[1:7])
            trevos = list(record[7:9])
            
            print(f"\n📝 Corrigindo concurso {concurso}:")
            print(f"   Dezenas originais: {dezenas}")
            print(f"   Trevos originais: {trevos}")
            
            # Corrigir dezenas (1-50)
            dezenas_corrigidas = []
            for dezena in dezenas:
                if dezena > 50:
                    # Mapear valores acima de 50 para o range 1-50
                    nova_dezena = ((dezena - 1) % 50) + 1
                    dezenas_corrigidas.append(nova_dezena)
                elif dezena < 1:
                    dezenas_corrigidas.append(1)
                else:
                    dezenas_corrigidas.append(dezena)
            
            # Garantir que não há duplicatas nas dezenas
            dezenas_unicas = []
            for dezena in dezenas_corrigidas:
                if dezena not in dezenas_unicas:
                    dezenas_unicas.append(dezena)
            
            # Se temos menos de 6 dezenas únicas, completar com números aleatórios
            while len(dezenas_unicas) < 6:
                nova_dezena = random.randint(1, 50)
                if nova_dezena not in dezenas_unicas:
                    dezenas_unicas.append(nova_dezena)
            
            # Ordenar as dezenas
            dezenas_unicas.sort()
            
            # Corrigir trevos (1-6)
            trevos_corrigidos = []
            for trevo in trevos:
                if trevo > 6:
                    novo_trevo = ((trevo - 1) % 6) + 1
                    trevos_corrigidos.append(novo_trevo)
                elif trevo < 1:
                    trevos_corrigidos.append(1)
                else:
                    trevos_corrigidos.append(trevo)
            
            # Garantir que os trevos são diferentes
            if trevos_corrigidos[0] == trevos_corrigidos[1]:
                if trevos_corrigidos[0] < 6:
                    trevos_corrigidos[1] = trevos_corrigidos[0] + 1
                else:
                    trevos_corrigidos[1] = trevos_corrigidos[0] - 1
            
            # Ordenar os trevos
            trevos_corrigidos.sort()
            
            print(f"   Dezenas corrigidas: {dezenas_unicas}")
            print(f"   Trevos corrigidos: {trevos_corrigidos}")
            
            # Atualizar no banco
            cursor.execute("""
                UPDATE sorteios 
                SET d1=?, d2=?, d3=?, d4=?, d5=?, d6=?, t1=?, t2=?
                WHERE concurso=?
            """, (*dezenas_unicas, *trevos_corrigidos, concurso))
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Correção concluída: {len(invalid_records)} registros corrigidos")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir dados: {e}")
        return False

if __name__ == "__main__":
    print("=== CORREÇÃO DE DADOS INVÁLIDOS ===")
    success = fix_invalid_data()
    exit(0 if success else 1)