"""Módulo para exportação de bilhetes em diferentes formatos.

Este módulo fornece funcionalidades para exportar bilhetes gerados
em formatos adequados para conferência e apostas.
"""

import pandas as pd
from pathlib import Path
from typing import List, Tuple, Union


def export_excel(tickets: List[Tuple], path: str = "outputs/jogos.xlsx") -> None:
    """
    Exporta bilhetes para arquivo Excel com formato padrão da +Milionária.
    
    Args:
        tickets: Lista de bilhetes no formato [(dezenas, trevos), ...]
                onde dezenas é uma tupla de 6 números e trevos uma tupla de 2 números
        path: Caminho do arquivo Excel de saída (padrão: "outputs/jogos.xlsx")
    
    Formato de saída:
        - Colunas D1, D2, D3, D4, D5, D6 para as dezenas
        - Colunas T1, T2 para os trevos
        - Uma linha por bilhete
    
    Example:
        >>> tickets = [((5, 10, 15, 20, 25, 30), (2, 5)), ((1, 6, 11, 16, 21, 26), (1, 3))]
        >>> export_excel(tickets, "meus_jogos.xlsx")
    """
    if not tickets:
        raise ValueError("Lista de bilhetes não pode estar vazia")
    
    # Criar diretório de saída se não existir
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Preparar dados para DataFrame
    data = []
    
    for ticket in tickets:
        if isinstance(ticket, tuple) and len(ticket) == 2:
            dezenas, trevos = ticket
        else:
            raise ValueError(f"Formato de bilhete inválido: {ticket}. Esperado: (dezenas, trevos)")
        
        # Validar dezenas
        if not isinstance(dezenas, (tuple, list)) or len(dezenas) != 6:
            raise ValueError(f"Dezenas inválidas: {dezenas}. Esperado: 6 números")
        
        # Validar trevos
        if not isinstance(trevos, (tuple, list)) or len(trevos) != 2:
            raise ValueError(f"Trevos inválidos: {trevos}. Esperado: 2 números")
        
        # Converter para inteiros se necessário
        try:
            dezenas_int = [int(d) for d in dezenas]
            trevos_int = [int(t) for t in trevos]
        except (ValueError, TypeError) as e:
            raise ValueError(f"Erro ao converter números: {e}")
        
        # Validar ranges
        for d in dezenas_int:
            if not (1 <= d <= 50):
                raise ValueError(f"Dezena {d} fora do range válido (1-50)")
        
        for t in trevos_int:
            if not (1 <= t <= 6):
                raise ValueError(f"Trevo {t} fora do range válido (1-6)")
        
        # Adicionar linha aos dados
        row = {
            'D1': dezenas_int[0],
            'D2': dezenas_int[1], 
            'D3': dezenas_int[2],
            'D4': dezenas_int[3],
            'D5': dezenas_int[4],
            'D6': dezenas_int[5],
            'T1': trevos_int[0],
            'T2': trevos_int[1]
        }
        data.append(row)
    
    # Criar DataFrame
    df = pd.DataFrame(data)
    
    # Garantir ordem das colunas
    columns_order = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2']
    df = df[columns_order]
    
    # Exportar para Excel
    try:
        df.to_excel(path, index=False, engine='openpyxl')
        print(f"✅ {len(tickets)} bilhetes exportados para: {path}")
    except Exception as e:
        raise RuntimeError(f"Erro ao salvar arquivo Excel: {e}")


def export_csv(tickets: List[Tuple], path: str = "outputs/jogos.csv") -> None:
    """
    Exporta bilhetes para arquivo CSV.
    
    Args:
        tickets: Lista de bilhetes no formato [(dezenas, trevos), ...]
        path: Caminho do arquivo CSV de saída
    """
    if not tickets:
        raise ValueError("Lista de bilhetes não pode estar vazia")
    
    # Criar diretório de saída se não existir
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Reutilizar lógica do Excel mas salvar como CSV
    data = []
    
    for ticket in tickets:
        if isinstance(ticket, tuple) and len(ticket) == 2:
            dezenas, trevos = ticket
        else:
            raise ValueError(f"Formato de bilhete inválido: {ticket}")
        
        dezenas_int = [int(d) for d in dezenas]
        trevos_int = [int(t) for t in trevos]
        
        row = {
            'D1': dezenas_int[0], 'D2': dezenas_int[1], 'D3': dezenas_int[2],
            'D4': dezenas_int[3], 'D5': dezenas_int[4], 'D6': dezenas_int[5],
            'T1': trevos_int[0], 'T2': trevos_int[1]
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    columns_order = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2']
    df = df[columns_order]
    
    try:
        df.to_csv(path, index=False)
        print(f"✅ {len(tickets)} bilhetes exportados para: {path}")
    except Exception as e:
        raise RuntimeError(f"Erro ao salvar arquivo CSV: {e}")


def format_ticket_display(ticket: Tuple) -> str:
    """
    Formata um bilhete para exibição legível.
    
    Args:
        ticket: Bilhete no formato (dezenas, trevos)
    
    Returns:
        String formatada do bilhete
    
    Example:
        >>> format_ticket_display(((5, 10, 15, 20, 25, 30), (2, 5)))
        '05-10-15-20-25-30 + 2-5'
    """
    if isinstance(ticket, tuple) and len(ticket) == 2:
        dezenas, trevos = ticket
    else:
        raise ValueError(f"Formato de bilhete inválido: {ticket}")
    
    # Formatar dezenas com zero à esquerda
    dezenas_str = '-'.join([f"{int(d):02d}" for d in dezenas])
    
    # Formatar trevos
    trevos_str = '-'.join([str(int(t)) for t in trevos])
    
    return f"{dezenas_str} + {trevos_str}"