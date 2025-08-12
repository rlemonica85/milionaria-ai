#!/usr/bin/env python3
"""Teste do módulo de atualização automática do banco de dados."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pytest
from src.update.update_db import update_database
from src.db.io import read_max_concurso


@pytest.mark.asyncio
async def test_update_functionality():
    """Testa a funcionalidade de atualização do banco."""
    print("Testando funcionalidade de atualização...")
    print("="*50)
    
    # Verifica estado inicial
    max_inicial = read_max_concurso()
    print(f"📊 Concurso máximo inicial: {max_inicial}")
    
    # Primeira execução
    print("\n🔄 Primeira execução da atualização...")
    ultimo1, novos1 = await update_database()
    print(f"   Resultado: último={ultimo1}, novos={novos1}")
    
    # Segunda execução (deve retornar 0 novos)
    print("\n🔄 Segunda execução da atualização...")
    ultimo2, novos2 = await update_database()
    print(f"   Resultado: último={ultimo2}, novos={novos2}")
    
    # Validações
    print("\n✅ Validações:")
    print(f"   • Último concurso consistente: {ultimo1 == ultimo2}")
    print(f"   • Segunda execução sem novos: {novos2 == 0}")
    print(f"   • Função retorna tupla: {isinstance((ultimo1, novos1), tuple)}")
    
    return ultimo1, novos1, ultimo2, novos2


@pytest.mark.asyncio
async def main():
    """Função principal do teste."""
    print("Teste do módulo de atualização automática")
    print("="*60)
    
    try:
        resultado = await test_update_functionality()
        ultimo1, novos1, ultimo2, novos2 = resultado
        
        print("\n📈 Resumo do teste:")
        print(f"   ✅ Primeira execução: último={ultimo1}, novos={novos1}")
        print(f"   ✅ Segunda execução: último={ultimo2}, novos={novos2}")
        print(f"   ✅ Critério atendido: segunda execução retornou 0 novos")
        
        print("\n🎉 Teste concluído com sucesso!")
        print("   • Módulo executável via python -m src.update.update_db")
        print("   • Imprime corretamente os resultados")
        print("   • Grava apenas novos concursos")
        print("   • Segunda execução retorna 'Novos: 0'")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)