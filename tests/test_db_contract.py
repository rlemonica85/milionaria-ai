#!/usr/bin/env python3
"""
Testes de contrato do banco de dados
Verifica se o banco atende aos requisitos mínimos de estrutura e dados
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path
import os
import sys

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audit.db_inspect import DatabaseInspector
from utils.validate import sanity_checks


class TestDatabaseContract:
    """Testes de contrato para o banco de dados"""
    
    @pytest.fixture(scope="class")
    def db_inspector(self):
        """Fixture para o inspetor de banco"""
        return DatabaseInspector()
    
    @pytest.fixture(scope="class")
    def db_path(self):
        """Fixture para o caminho do banco"""
        project_root = Path(__file__).parent.parent
        return project_root / "db" / "milionaria.db"
    
    def test_database_exists(self, db_inspector):
        """Teste: Banco de dados deve existir"""
        assert db_inspector.check_database_exists(), "Database file not found"
    
    def test_database_readable(self, db_path):
        """Teste: Banco deve ser legível"""
        assert db_path.exists(), "Database file not found"
        
        # Tentar conectar
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1, "Database connection failed"
        except Exception as e:
            pytest.fail(f"Failed to connect to database: {e}")
    
    def test_required_tables_exist(self, db_path):
        """Teste: Tabelas obrigatórias devem existir"""
        required_tables = ['sorteios']
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            assert table in existing_tables, f"Required table '{table}' not found"
    
    def test_sorteios_table_structure(self, db_path):
        """Teste: Estrutura da tabela sorteios"""
        expected_columns = {
             'concurso': 'INTEGER',
             'data': 'DATE',
             'd1': 'INTEGER',
             'd2': 'INTEGER', 
             'd3': 'INTEGER',
             'd4': 'INTEGER',
             'd5': 'INTEGER',
             'd6': 'INTEGER',
             't1': 'INTEGER',
             't2': 'INTEGER'
         }
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sorteios)")
            columns = cursor.fetchall()
        
        # Converter para dict {nome: tipo}
        actual_columns = {col[1]: col[2] for col in columns}
        
        for col_name, col_type in expected_columns.items():
            assert col_name in actual_columns, f"Column '{col_name}' not found"
            assert actual_columns[col_name] == col_type, f"Column '{col_name}' has wrong type: {actual_columns[col_name]} (expected {col_type})"
    
    def test_minimum_data_count(self, db_path):
        """Teste: Deve ter pelo menos 275 registros"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sorteios")
            count = cursor.fetchone()[0]
        
        assert count >= 275, f"Insufficient data: {count} rows (minimum 275 required)"
    
    def test_no_duplicate_concursos(self, db_path):
        """Teste: Não deve haver concursos duplicados"""
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query("SELECT concurso, COUNT(*) as count FROM sorteios GROUP BY concurso HAVING COUNT(*) > 1", conn)
        
        assert len(df) == 0, f"Found {len(df)} duplicate concursos: {df['concurso'].tolist()}"
    
    def test_dezenas_range(self, db_path):
        """Teste: Dezenas devem estar no range [1,50]"""
        dezena_cols = [f'd{i}' for i in range(1, 7)]
        
        with sqlite3.connect(db_path) as conn:
            for col in dezena_cols:
                # Verificar valores fora do range
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM sorteios WHERE {col} < 1 OR {col} > 50")
                out_of_range = cursor.fetchone()[0]
                
                assert out_of_range == 0, f"Column {col} has {out_of_range} values outside range [1,50]"
                
                # Verificar valores nulos
                cursor.execute(f"SELECT COUNT(*) FROM sorteios WHERE {col} IS NULL")
                nulls = cursor.fetchone()[0]
                
                assert nulls == 0, f"Column {col} has {nulls} null values"
    
    def test_trevos_range(self, db_path):
        """Teste: Trevos devem estar no range [1,6]"""
        trevo_cols = [f't{i}' for i in range(1, 3)]
        
        with sqlite3.connect(db_path) as conn:
            for col in trevo_cols:
                # Verificar valores fora do range
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM sorteios WHERE {col} < 1 OR {col} > 6")
                out_of_range = cursor.fetchone()[0]
                
                assert out_of_range == 0, f"Column {col} has {out_of_range} values outside range [1,6]"
                
                # Verificar valores nulos
                cursor.execute(f"SELECT COUNT(*) FROM sorteios WHERE {col} IS NULL")
                nulls = cursor.fetchone()[0]
                
                assert nulls == 0, f"Column {col} has {nulls} null values"
    
    def test_concurso_numbers_positive(self, db_path):
        """Teste: Números de concurso devem ser positivos"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sorteios WHERE concurso <= 0")
            invalid_count = cursor.fetchone()[0]
        
        assert invalid_count == 0, f"Found {invalid_count} concursos with non-positive numbers"
    
    def test_dezenas_unique_per_concurso(self, db_path):
        """Teste: Dezenas devem ser únicas dentro de cada concurso"""
        with sqlite3.connect(db_path) as conn:
            # Verificar se há dezenas repetidas no mesmo concurso
            query = """
            SELECT concurso, COUNT(*) as duplicates
            FROM (
                SELECT concurso, d1 as dezena FROM sorteios
                UNION ALL SELECT concurso, d2 FROM sorteios
                UNION ALL SELECT concurso, d3 FROM sorteios
                UNION ALL SELECT concurso, d4 FROM sorteios
                UNION ALL SELECT concurso, d5 FROM sorteios
                UNION ALL SELECT concurso, d6 FROM sorteios
            ) t
            GROUP BY concurso, dezena
            HAVING COUNT(*) > 1
            """
            
            df = pd.read_sql_query(query, conn)
        
        assert len(df) == 0, f"Found {len(df)} concursos with duplicate dezenas"
    
    def test_trevos_unique_per_concurso(self, db_path):
        """Teste: Trevos devem ser únicos dentro de cada concurso"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sorteios WHERE t1 = t2")
            duplicate_trevos = cursor.fetchone()[0]
        
        assert duplicate_trevos == 0, f"Found {duplicate_trevos} concursos with duplicate trevos"
    
    def test_sanity_checks_pass(self):
        """Teste: Verificações de sanidade devem passar"""
        try:
            result = sanity_checks()
            assert result is True, "Sanity checks failed"
        except Exception as e:
            pytest.fail(f"Sanity checks raised exception: {e}")
    
    def test_data_export_works(self, db_inspector):
        """Teste: Export de dados deve funcionar"""
        result = db_inspector.export_sample_data()
        
        assert "error" not in result, f"Export failed: {result.get('error', 'Unknown error')}"
        assert "full_export" in result, "Full export path not returned"
        assert "preview_export" in result, "Preview export path not returned"
        
        # Verificar se arquivos foram criados
        full_path = Path(result["full_export"])
        preview_path = Path(result["preview_export"])
        
        assert full_path.exists(), f"Full export file not created: {full_path}"
        assert preview_path.exists(), f"Preview export file not created: {preview_path}"
        
        # Verificar se arquivos não estão vazios
        assert full_path.stat().st_size > 0, "Full export file is empty"
        assert preview_path.stat().st_size > 0, "Preview export file is empty"
    
    def test_database_integrity_check(self, db_inspector):
        """Teste: Verificação de integridade completa"""
        audit_results = db_inspector.run_full_audit()
        
        assert "audit_status" in audit_results, "Audit status not found"
        
        status = audit_results["audit_status"]
        assert status["passed"] is True, f"Database integrity check failed. Issues: {status['issues']}"
        assert status["issues_found"] == 0, f"Found {status['issues_found']} integrity issues"


class TestDatabasePerformance:
    """Testes de performance básica do banco"""
    
    @pytest.fixture(scope="class")
    def db_path(self):
        """Fixture para o caminho do banco"""
        project_root = Path(__file__).parent.parent
        return project_root / "db" / "milionaria.db"
    
    def test_query_performance_basic(self, db_path):
        """Teste: Consultas básicas devem ser rápidas"""
        import time
        
        with sqlite3.connect(db_path) as conn:
            # Teste de contagem simples
            start_time = time.time()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sorteios")
            cursor.fetchone()
            count_time = time.time() - start_time
            
            # Teste de seleção com ordenação
            start_time = time.time()
            cursor.execute("SELECT * FROM sorteios ORDER BY concurso LIMIT 10")
            cursor.fetchall()
            select_time = time.time() - start_time
        
        # Consultas devem ser rápidas (menos de 1 segundo)
        assert count_time < 1.0, f"COUNT query too slow: {count_time:.2f}s"
        assert select_time < 1.0, f"SELECT query too slow: {select_time:.2f}s"


if __name__ == "__main__":
    # Executar testes se chamado diretamente
    pytest.main([__file__, "-v"])