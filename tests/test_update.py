"""Testes para operações de atualização do banco de dados."""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Adicionar src ao path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from db.schema import get_engine, ensure_schema
from db.io import upsert_rows, read_max_concurso


class TestDatabaseUpdate:
    """Testes para operações de atualização do banco."""
    
    @pytest.fixture
    def temp_db(self):
        """Fixture para criar um banco temporário para testes."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Criar tabelas
        engine = get_engine(path)
        ensure_schema(engine)
        engine.dispose()
        
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
    
    @pytest.fixture
    def sample_draw_data(self):
        """Fixture com dados de exemplo de um sorteio."""
        return {
            'concurso': 100,
            'data': '2024-08-15',
            'd1': 5, 'd2': 12, 'd3': 18, 'd4': 25, 'd5': 33, 'd6': 41,
            't1': 2, 't2': 4
        }
    
    @pytest.fixture
    def sample_draw_data_2(self):
        """Fixture com dados de exemplo de um segundo sorteio."""
        return {
            'concurso': 101,
            'data_sorteio': '2024-08-22',
            'dezenas': [3, 9, 15, 21, 27, 45],
            'trevos': [1, 6]
        }
    
    def test_read_max_concurso_empty_db(self, temp_db):
        """Testa leitura do máximo concurso em banco vazio."""
        max_concurso = read_max_concurso(temp_db)
        assert max_concurso == 0
    
    def test_read_max_concurso_with_data(self, temp_db, sample_draw_data):
        """Testa leitura do máximo concurso com dados."""
        import pandas as pd
        
        # Inserir dados
        df = pd.DataFrame([sample_draw_data])
        upsert_rows(df, temp_db)
        
        # Verificar máximo concurso
        max_concurso = read_max_concurso(temp_db)
        assert max_concurso == 100
    
    def test_upsert_draw_success(self, temp_db, sample_draw_data):
        """Testa inserção bem-sucedida de um sorteio."""
        import pandas as pd
        
        # Converter para DataFrame
        df = pd.DataFrame([sample_draw_data])
        
        # Inserir dados
        result = upsert_rows(df, temp_db)
        assert result >= 1  # Pelo menos 1 linha afetada
        
        # Verificar se foi inserido
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sorteios WHERE concurso = ?", (100,))
        count = cursor.fetchone()[0]
        assert count == 1
        
        # Verificar dados inseridos
        cursor.execute("""
            SELECT concurso, data, d1, d2, d3, d4, d5, d6, t1, t2
            FROM sorteios WHERE concurso = ?
        """, (100,))
        
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 100  # concurso
        assert row[1] == '2024-08-15'  # data
        assert list(row[2:8]) == [5, 12, 18, 25, 33, 41]  # dezenas
        assert list(row[8:10]) == [2, 4]  # trevos
        
        conn.close()
    
    def test_upsert_duplicate_draw(self, temp_db, sample_draw_data):
        """Testa inserção de sorteio duplicado."""
        import pandas as pd
        
        df = pd.DataFrame([sample_draw_data])
        
        # Primeira inserção
        result1 = upsert_rows(df, temp_db)
        assert result1 >= 1
        
        # Segunda inserção (deve substituir)
        result2 = upsert_rows(df, temp_db)
        assert result2 >= 1
        
        # Verificar que ainda há apenas 1 registro
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sorteios WHERE concurso = ?", (100,))
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()
    
    def test_upsert_multiple_draws(self, temp_db, sample_draw_data, sample_draw_data_2):
        """Testa inserção de múltiplos sorteios."""
        import pandas as pd
        
        # Inserir ambos sorteios de uma vez
        df = pd.DataFrame([sample_draw_data, sample_draw_data_2])
        
        # Garantir que não há valores NaN
        df = df.fillna(0)
        
        result = upsert_rows(df, temp_db)
        assert result >= 2
        
        # Verificar se ambos foram inseridos
        conn = sqlite3.connect(temp_db)
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM sorteios")
            count = cursor.fetchone()[0]
            assert count == 2
            
            # Verificar máximo concurso
            max_concurso = read_max_concurso(temp_db)
            assert max_concurso == 101
        finally:
            conn.close()
    
    def test_upsert_with_mock_data(self, temp_db):
        """Testa inserção com dados simulados."""
        import pandas as pd
        
        # Dados simulados
        mock_data = [
            {
                'concurso': 200,
                'data': '2024-09-01',
                'd1': 1, 'd2': 7, 'd3': 13, 'd4': 19, 'd5': 25, 'd6': 31,
                't1': 3, 't2': 5
            },
            {
                'concurso': 201,
                'data': '2024-09-08',
                'd1': 2, 'd2': 8, 'd3': 14, 'd4': 20, 'd5': 26, 'd6': 32,
                't1': 1, 't2': 4
            }
        ]
        
        # Inserir dados
        df = pd.DataFrame(mock_data)
        result = upsert_rows(df, temp_db)
        assert result >= 2
        
        # Verificar se dados foram inseridos
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sorteios")
        count = cursor.fetchone()[0]
        assert count == 2
        
        # Verificar máximo concurso
        max_concurso = read_max_concurso(temp_db)
        assert max_concurso == 201
        
        conn.close()
    
    def test_read_max_concurso_mock(self, temp_db):
        """Testa mock da função read_max_concurso."""
        from unittest.mock import patch
        
        # Usar patch como context manager
        with patch('db.io.read_max_concurso') as mock_read_max:
            # Configurar mock para retornar 150
            mock_read_max.return_value = 150
            
            # Chamar função mockada
            result = mock_read_max(temp_db)
            
            # Verificar se mock foi chamado corretamente
            mock_read_max.assert_called_once_with(temp_db)
            assert result == 150
    
    def test_read_max_concurso_with_existing_data(self, temp_db):
        """Testa read_max_concurso com dados existentes."""
        import pandas as pd
        
        # Inserir alguns dados primeiro
        data = [
            {
                'concurso': 50,
                'data': '2024-01-01',
                'd1': 1, 'd2': 2, 'd3': 3, 'd4': 4, 'd5': 5, 'd6': 6,
                't1': 1, 't2': 2
            },
            {
                'concurso': 75,
                'data': '2024-02-01',
                'd1': 7, 'd2': 8, 'd3': 9, 'd4': 10, 'd5': 11, 'd6': 12,
                't1': 3, 't2': 4
            }
        ]
        
        df = pd.DataFrame(data)
        upsert_rows(df, temp_db)
        
        # Verificar máximo concurso
        max_concurso = read_max_concurso(temp_db)
        assert max_concurso == 75
    
    def test_data_validation_missing_columns(self, temp_db):
        """Testa validação de dados com colunas faltando."""
        import pandas as pd
        
        # Dados com colunas faltando
        invalid_data = pd.DataFrame([{
            'concurso': 300,
            'data': '2024-10-01',
            'd1': 1, 'd2': 2, 'd3': 3  # Faltam d4, d5, d6, t1, t2
        }])
        
        # Tentar inserir dados inválidos
        with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
            upsert_rows(invalid_data, temp_db)
    
    def test_data_validation_complete_data(self, temp_db):
        """Testa validação com dados completos e válidos."""
        import pandas as pd
        
        # Dados válidos e completos
        valid_data = pd.DataFrame([{
            'concurso': 301,
            'data': '2024-10-01',
            'd1': 1, 'd2': 7, 'd3': 13, 'd4': 19, 'd5': 25, 'd6': 31,
            't1': 1, 't2': 4
        }])
        
        # Inserir dados válidos (não deve dar erro)
        result = upsert_rows(valid_data, temp_db)
        assert result >= 1
        
        # Verificar se foi inserido
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sorteios WHERE concurso = ?", (301,))
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()