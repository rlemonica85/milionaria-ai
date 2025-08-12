#!/usr/bin/env python3
"""
Módulo de inspeção e auditoria do banco de dados
Verifica integridade, estrutura e qualidade dos dados
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInspector:
    """Inspetor de banco de dados para auditoria completa"""
    
    def __init__(self, db_path: str = "db/milionaria.db"):
        self.db_path = Path(db_path)
        self.project_root = Path(__file__).parent.parent.parent
        self.full_db_path = self.project_root / self.db_path
        
    def check_database_exists(self) -> bool:
        """Verifica se o banco de dados existe"""
        exists = self.full_db_path.exists()
        logger.info(f"Database exists: {exists} at {self.full_db_path}")
        return exists
    
    def get_database_info(self) -> Dict[str, Any]:
        """Obtém informações básicas do banco"""
        if not self.check_database_exists():
            return {"error": "Database not found"}
        
        try:
            size = self.full_db_path.stat().st_size
            modified = datetime.fromtimestamp(self.full_db_path.stat().st_mtime)
            
            return {
                "path": str(self.full_db_path),
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "last_modified": modified.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": f"Failed to get database info: {e}"}
    
    def get_table_info(self) -> Dict[str, Any]:
        """Obtém informações sobre as tabelas"""
        try:
            with sqlite3.connect(self.full_db_path) as conn:
                cursor = conn.cursor()
                
                # Listar tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                table_info = {}
                for table in tables:
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    # Obter schema
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    table_info[table] = {
                        "row_count": count,
                        "columns": [
                            {
                                "name": col[1],
                                "type": col[2],
                                "not_null": bool(col[3]),
                                "primary_key": bool(col[5])
                            }
                            for col in columns
                        ]
                    }
                
                return {
                    "tables": tables,
                    "table_count": len(tables),
                    "details": table_info
                }
        except Exception as e:
            return {"error": f"Failed to get table info: {e}"}
    
    def check_data_integrity(self) -> Dict[str, Any]:
        """Verifica integridade dos dados principais"""
        try:
            with sqlite3.connect(self.full_db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM sorteios", conn)
                
                if df.empty:
                    return {"error": "No data found in sorteios table"}
                
                # Verificações básicas
                total_rows = len(df)
                
                # Verificar duplicatas de concurso
                duplicates = df['concurso'].duplicated().sum()
                
                # Verificar ranges de dezenas (1-50)
                dezena_cols = [f'd{i}' for i in range(1, 7)]
                dezena_issues = {}
                
                for col in dezena_cols:
                    if col in df.columns:
                        out_of_range = ((df[col] < 1) | (df[col] > 50)).sum()
                        nulls = df[col].isnull().sum()
                        dezena_issues[col] = {
                            "out_of_range": out_of_range,
                            "nulls": nulls
                        }
                
                # Verificar ranges de trevos (1-6)
                trevo_cols = [f't{i}' for i in range(1, 3)]
                trevo_issues = {}
                
                for col in trevo_cols:
                    if col in df.columns:
                        out_of_range = ((df[col] < 1) | (df[col] > 6)).sum()
                        nulls = df[col].isnull().sum()
                        trevo_issues[col] = {
                            "out_of_range": out_of_range,
                            "nulls": nulls
                        }
                
                # Verificar concursos sequenciais
                if 'concurso' in df.columns:
                    sorted_df = df.sort_values('concurso')
                    gaps = []
                    for i in range(1, len(sorted_df)):
                        current = sorted_df.iloc[i]['concurso']
                        previous = sorted_df.iloc[i-1]['concurso']
                        if current - previous > 1:
                            gaps.append((previous, current))
                
                return {
                    "total_rows": total_rows,
                    "duplicate_concursos": duplicates,
                    "dezena_issues": dezena_issues,
                    "trevo_issues": trevo_issues,
                    "sequential_gaps": gaps[:10],  # Primeiros 10 gaps
                    "total_gaps": len(gaps),
                    "min_concurso": int(df['concurso'].min()) if 'concurso' in df.columns else None,
                    "max_concurso": int(df['concurso'].max()) if 'concurso' in df.columns else None
                }
                
        except Exception as e:
            return {"error": f"Failed to check data integrity: {e}"}
    
    def export_sample_data(self, output_dir: str = "outputs", sample_size: int = 10) -> Dict[str, Any]:
        """Exporta amostra dos dados para inspeção"""
        try:
            output_path = self.project_root / output_dir
            output_path.mkdir(exist_ok=True)
            
            with sqlite3.connect(self.full_db_path) as conn:
                # Export completo
                df_full = pd.read_sql_query("SELECT * FROM sorteios ORDER BY concurso", conn)
                full_csv_path = output_path / "dump.csv"
                df_full.to_csv(full_csv_path, index=False)
                
                # Export preview (primeiras linhas)
                df_preview = df_full.head(sample_size)
                preview_csv_path = output_path / "dump_preview.csv"
                df_preview.to_csv(preview_csv_path, index=False)
                
                return {
                    "full_export": str(full_csv_path),
                    "preview_export": str(preview_csv_path),
                    "full_rows": len(df_full),
                    "preview_rows": len(df_preview)
                }
                
        except Exception as e:
            return {"error": f"Failed to export data: {e}"}
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Executa auditoria completa"""
        logger.info("Starting full database audit...")
        
        audit_results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "database_info": self.get_database_info(),
            "table_info": self.get_table_info(),
            "data_integrity": self.check_data_integrity(),
            "export_results": self.export_sample_data()
        }
        
        # Determinar status geral
        issues = []
        
        # Verificar se DB existe
        if "error" in audit_results["database_info"]:
            issues.append("Database not found")
        
        # Verificar contagem mínima
        table_info = audit_results["table_info"]
        if "error" not in table_info and "details" in table_info:
            concursos_count = table_info["details"].get("sorteios", {}).get("row_count", 0)
            if concursos_count < 275:
                issues.append(f"Insufficient data: {concursos_count} rows (minimum 275)")
        
        # Verificar integridade
        integrity = audit_results["data_integrity"]
        if "error" not in integrity:
            if integrity.get("duplicate_concursos", 0) > 0:
                issues.append(f"Found {integrity['duplicate_concursos']} duplicate concursos")
            
            # Verificar dezenas
            for col, issues_data in integrity.get("dezena_issues", {}).items():
                if issues_data["out_of_range"] > 0:
                    issues.append(f"{col}: {issues_data['out_of_range']} values out of range [1,50]")
                if issues_data["nulls"] > 0:
                    issues.append(f"{col}: {issues_data['nulls']} null values")
            
            # Verificar trevos
            for col, issues_data in integrity.get("trevo_issues", {}).items():
                if issues_data["out_of_range"] > 0:
                    issues.append(f"{col}: {issues_data['out_of_range']} values out of range [1,6]")
                if issues_data["nulls"] > 0:
                    issues.append(f"{col}: {issues_data['nulls']} null values")
        
        audit_results["audit_status"] = {
            "passed": len(issues) == 0,
            "issues_found": len(issues),
            "issues": issues
        }
        
        logger.info(f"Audit completed. Status: {'PASS' if len(issues) == 0 else 'FAIL'}")
        if issues:
            for issue in issues:
                logger.warning(f"Issue: {issue}")
        
        return audit_results


def main():
    """Função principal para execução via linha de comando"""
    inspector = DatabaseInspector()
    results = inspector.run_full_audit()
    
    # Imprimir resultados formatados
    print("\n" + "="*60)
    print("DATABASE AUDIT REPORT")
    print("="*60)
    
    # Status geral
    status = results["audit_status"]
    print(f"\nOVERALL STATUS: {'✅ PASS' if status['passed'] else '❌ FAIL'}")
    print(f"Issues found: {status['issues_found']}")
    
    if status['issues']:
        print("\nISSUES:")
        for i, issue in enumerate(status['issues'], 1):
            print(f"  {i}. {issue}")
    
    # Informações do banco
    db_info = results["database_info"]
    if "error" not in db_info:
        print(f"\nDATABASE INFO:")
        print(f"  Path: {db_info['path']}")
        print(f"  Size: {db_info['size_mb']} MB")
        print(f"  Last modified: {db_info['last_modified']}")
    
    # Informações das tabelas
    table_info = results["table_info"]
    if "error" not in table_info:
        print(f"\nTABLE INFO:")
        for table, details in table_info["details"].items():
            print(f"  {table}: {details['row_count']} rows")
    
    # Integridade dos dados
    integrity = results["data_integrity"]
    if "error" not in integrity:
        print(f"\nDATA INTEGRITY:")
        print(f"  Total rows: {integrity['total_rows']}")
        print(f"  Duplicate concursos: {integrity['duplicate_concursos']}")
        print(f"  Concurso range: {integrity['min_concurso']} - {integrity['max_concurso']}")
        print(f"  Sequential gaps: {integrity['total_gaps']}")
    
    # Exports
    export_info = results["export_results"]
    if "error" not in export_info:
        print(f"\nEXPORTS:")
        print(f"  Full dump: {export_info['full_export']} ({export_info['full_rows']} rows)")
        print(f"  Preview: {export_info['preview_export']} ({export_info['preview_rows']} rows)")
    
    print("\n" + "="*60)
    
    return 0 if status['passed'] else 1


if __name__ == "__main__":
    exit(main())