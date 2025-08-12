"""Módulo para definição do schema do banco de dados."""

import os
from sqlalchemy import create_engine, Column, Integer, Date, MetaData, Table
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def get_engine(db_path="db/milionaria.db"):
    """Cria e retorna engine do SQLite.
    
    Args:
        db_path (str): Caminho para o arquivo do banco de dados
        
    Returns:
        sqlalchemy.engine.Engine: Engine configurado para SQLite
    """
    # Garante que o diretório existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Cria engine SQLite
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return engine


def ensure_schema(engine):
    """Cria a tabela sorteios se não existir.
    
    Args:
        engine: Engine do SQLAlchemy
    """
    metadata = MetaData()
    
    # Define a tabela sorteios
    sorteios = Table(
        'sorteios',
        metadata,
        Column('concurso', Integer, primary_key=True),
        Column('data', Date, nullable=False),
        Column('d1', Integer, nullable=False),
        Column('d2', Integer, nullable=False),
        Column('d3', Integer, nullable=False),
        Column('d4', Integer, nullable=False),
        Column('d5', Integer, nullable=False),
        Column('d6', Integer, nullable=False),
        Column('t1', Integer, nullable=False),
        Column('t2', Integer, nullable=False)
    )
    
    # Cria as tabelas
    metadata.create_all(engine)
    print(f"Schema criado/verificado com sucesso!")


if __name__ == "__main__":
    # Teste básico
    engine = get_engine()
    ensure_schema(engine)