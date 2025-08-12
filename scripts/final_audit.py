#!/usr/bin/env python3
"""Script para executar auditoria final do sistema."""

import sys
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from audit.db_inspect import DatabaseInspector

def main():
    print("=== AUDITORIA FINAL DO SISTEMA ===")
    
    inspector = DatabaseInspector()
    result = inspector.run_full_audit()
    
    status = result["audit_status"]
    
    print(f"✅ Status da Auditoria: {'PASSOU' if status['passed'] else 'FALHOU'}")
    print(f"📊 Issues Encontrados: {status['issues_found']}")
    
    if status['issues']:
        print("\n⚠️  Issues Detectados:")
        for issue in status['issues']:
            print(f"   - {issue}")
    else:
        print("\n🎉 Nenhum problema encontrado!")
    
    print("\n=== RESUMO ===")
    print(f"Database Info: {'✅' if 'error' not in result['database_info'] else '❌'}")
    print(f"Table Info: {'✅' if 'error' not in result['table_info'] else '❌'}")
    print(f"Data Integrity: {'✅' if 'error' not in result['data_integrity'] else '❌'}")
    
    print("\n🔍 Auditoria concluída!")
    return status['passed']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)