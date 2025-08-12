"""Testes para criação e estrutura do schema do banco de dados."""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

# Adicionar src ao path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from db.schema import get_engine, ensure_schema
from db.io import read_max_concurso


class TestSchema:
    """Testes para criação e validação do schema do banco."""
    
    @pytest.fixture
    def temp_db(self):
        """Fixture para criar um banco temporário para testes."""
        # Criar arquivo temporário
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        yield path
        
        # Cleanup - aguardar um pouco e tentar fechar conexões
        import time
        time.sleep(0.1)
        try:
            if os.path.exists(path):
                os.unlink(path)
        except PermissionError:
            # Se não conseguir deletar, não é crítico para o teste
            pass
    
    def test_create_tables_success(self, temp_db):
        """Testa se as tabelas são criadas com sucesso."""
        # Criar tabelas
        engine = get_engine(temp_db)
        ensure_schema(engine)
        
        # Verificar se o arquivo foi criado
        assert os.path.exists(temp_db)
        
        # Conectar e verificar estrutura
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Verificar se a tabela 'sorteios' existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sorteios'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'sorteios'
        
        conn.close()
        engine.dispose()
    
    def test_sorteios_table_structure(self, temp_db):
        """Testa a estrutura da tabela sorteios."""
        engine = get_engine(temp_db)
        ensure_schema(engine)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Obter informações das colunas
        cursor.execute("PRAGMA table_info(sorteios)")
        columns = cursor.fetchall()
        
        # Verificar se as colunas esperadas existem
        column_names = [col[1] for col in columns]
        expected_columns = [
            'concurso', 'data', 'd1', 'd2', 'd3',
            'd4', 'd5', 'd6', 't1', 't2'
        ]
        
        for expected_col in expected_columns:
            assert expected_col in column_names, f"Coluna {expected_col} não encontrada"
        
        # Verificar se concurso é chave primária
        primary_key_cols = [col[1] for col in columns if col[5] == 1]
        assert 'concurso' in primary_key_cols
        
        conn.close()
        engine.dispose()
    
    def test_get_engine_with_new_db(self, temp_db):
        """Testa a função get_engine com um banco novo."""
        # Remover arquivo se existir
        if os.path.exists(temp_db):
            os.unlink(temp_db)
        
        # Tentar conectar (deve criar o banco)
        engine = get_engine(temp_db)
        assert engine is not None
        
        # Verificar se arquivo foi criado após ensure_schema
        ensure_schema(engine)
        assert os.path.exists(temp_db)
        
        engine.dispose()
    
    def test_multiple_table_creation_calls(self, temp_db):
        """Testa se múltiplas chamadas de ensure_schema não causam erro."""
        engine = get_engine(temp_db)
        
        # Primeira criação
        ensure_schema(engine)
        
        # Segunda criação (não deve dar erro)
        ensure_schema(engine)
        
        # Verificar se tabela ainda existe
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sorteios'
        """)
        result = cursor.fetchone()
        assert result is not None
        
        conn.close()
        engine.dispose()
    
    def test_table_constraints(self, temp_db):
        """Testa se as constraints da tabela funcionam corretamente."""
        engine = get_engine(temp_db)
        ensure_schema(engine)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Tentar inserir dados válidos
        cursor.execute("""
            INSERT INTO sorteios (
                concurso, data, d1, d2, d3,
                d4, d5, d6, t1, t2
            ) VALUES (1, '2023-01-01', 1, 2, 3, 4, 5, 6, 1, 2)
        """)
        
        # Verificar se foi inserido
        cursor.execute("SELECT COUNT(*) FROM sorteios")
        count = cursor.fetchone()[0]
        assert count == 1
        
        # Tentar inserir concurso duplicado (deve falhar)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO sorteios (
                    concurso, data, d1, d2, d3,
                    d4, d5, d6, t1, t2
                ) VALUES (1, '2023-01-02', 7, 8, 9, 10, 11, 12, 3, 4)
            """)
        
        conn.close()
        engine.dispose()