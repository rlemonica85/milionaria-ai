"""Seletores e padrões para extração de dados do portal da CAIXA (+Milionária)."""

import re
from typing import Dict, Optional, Tuple

# URL da página da +Milionária no portal da CAIXA
CAIXA_MILIONARIA_URL = "https://loterias.caixa.gov.br/Paginas/Mais-Milionaria.aspx"

# Padrões regex resilientes para extração de dados
PATTERNS = {
    # Padrão para número do concurso
    'concurso': [
        r'Concurso\s+(\d+)',
        r'CONCURSO\s+(\d+)',
        r'concurso\s+(\d+)',
        r'Nº\s*(\d+)',
        r'N°\s*(\d+)',
        r'#(\d+)',
        r'(\d{3,4})\s*-\s*\d{2}/\d{2}/\d{4}',  # formato: 123 - 01/01/2023
    ],
    
    # Padrão para data do sorteio
    'data': [
        r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
        r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'Data\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
        r'Sorteio\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
    ],
    
    # Padrão para as 6 dezenas principais (1-50)
    'dezenas': [
        # Sequência de 6 números separados por espaços/vírgulas
        r'(?:Dezenas?[:\s]*)?([0-5]?\d)\s*[,\s]+([0-5]?\d)\s*[,\s]+([0-5]?\d)\s*[,\s]+([0-5]?\d)\s*[,\s]+([0-5]?\d)\s*[,\s]+([0-5]?\d)',
        # Números em divs/spans separados
        r'<[^>]*>\s*([0-5]?\d)\s*</[^>]*>\s*<[^>]*>\s*([0-5]?\d)\s*</[^>]*>\s*<[^>]*>\s*([0-5]?\d)\s*</[^>]*>\s*<[^>]*>\s*([0-5]?\d)\s*</[^>]*>\s*<[^>]*>\s*([0-5]?\d)\s*</[^>]*>\s*<[^>]*>\s*([0-5]?\d)\s*</[^>]*>',
        # Formato com zeros à esquerda
        r'(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})',
    ],
    
    # Padrão para os 2 trevos (1-6)
    'trevos': [
        # Sequência de 2 números após "trevo" ou similar
        r'(?:Trevo[s]?[:\s]*)([1-6])\s*[,\s]+([1-6])',
        r'(?:Trevos?[:\s]*)([1-6])\s*[,\s]*([1-6])',
        # Formato específico da CAIXA
        r'<[^>]*trevo[^>]*>\s*([1-6])\s*</[^>]*>\s*<[^>]*>\s*([1-6])\s*</[^>]*>',
        # Números isolados após as dezenas
        r'\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+([1-6])\s+([1-6])',
    ]
}

# Seletores CSS para elementos da página
CSS_SELECTORS = {
    'resultado_container': [
        '.resultado-loteria',
        '.resultado',
        '.content-resultado',
        '#resultado',
        '.sorteio-resultado'
    ],
    
    'navegacao_anterior': [
        'a[title*="anterior"]',
        'button[title*="anterior"]',
        '.btn-anterior',
        '.anterior',
        'a:contains("Anterior")',
        'button:contains("Anterior")',
        '.navigation .prev'
    ],
    
    'navegacao_proximo': [
        'a[title*="próximo"]',
        'a[title*="proximo"]',
        'button[title*="próximo"]',
        'button[title*="proximo"]',
        '.btn-proximo',
        '.proximo',
        'a:contains("Próximo")',
        'button:contains("Próximo")',
        '.navigation .next'
    ],
    
    'numero_concurso': [
        '.numero-concurso',
        '.concurso',
        '#concurso',
        '.sorteio-numero'
    ],
    
    'data_sorteio': [
        '.data-sorteio',
        '.data',
        '#data',
        '.sorteio-data'
    ],
    
    'dezenas_container': [
        '.dezenas',
        '.numeros-sorteados',
        '.resultado-numeros',
        '.bolas'
    ],
    
    'trevos_container': [
        '.trevos',
        '.trevo',
        '.numeros-trevo'
    ]
}


def extract_concurso(text: str) -> Optional[int]:
    """Extrai número do concurso do texto.
    
    Args:
        text (str): Texto da página
        
    Returns:
        Optional[int]: Número do concurso ou None se não encontrado
    """
    for pattern in PATTERNS['concurso']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    return None


def extract_data(text: str) -> Optional[str]:
    """Extrai data do sorteio do texto.
    
    Args:
        text (str): Texto da página
        
    Returns:
        Optional[str]: Data do sorteio ou None se não encontrada
    """
    for pattern in PATTERNS['data']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_dezenas(text: str) -> Optional[Tuple[int, ...]]:
    """Extrai as 6 dezenas do texto.
    
    Args:
        text (str): Texto da página
        
    Returns:
        Optional[Tuple[int, ...]]: Tupla com 6 dezenas ou None se não encontradas
    """
    for pattern in PATTERNS['dezenas']:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match and len(match.groups()) == 6:
            try:
                dezenas = tuple(int(g) for g in match.groups())
                # Valida se todas as dezenas estão no range 1-50
                if all(1 <= d <= 50 for d in dezenas):
                    return dezenas
            except (ValueError, TypeError):
                continue
    return None


def extract_trevos(text: str) -> Optional[Tuple[int, int]]:
    """Extrai os 2 trevos do texto.
    
    Args:
        text (str): Texto da página
        
    Returns:
        Optional[Tuple[int, int]]: Tupla com 2 trevos ou None se não encontrados
    """
    for pattern in PATTERNS['trevos']:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match and len(match.groups()) == 2:
            try:
                trevos = tuple(int(g) for g in match.groups())
                # Valida se ambos os trevos estão no range 1-6
                if all(1 <= t <= 6 for t in trevos):
                    return trevos
            except (ValueError, TypeError):
                continue
    return None


def extract_all_data(text: str) -> Dict[str, any]:
    """Extrai todos os dados do texto da página.
    
    Args:
        text (str): Texto da página
        
    Returns:
        Dict[str, any]: Dicionário com todos os dados extraídos
    """
    result = {
        'concurso': extract_concurso(text),
        'data': extract_data(text),
        'dezenas': extract_dezenas(text),
        'trevos': extract_trevos(text)
    }
    
    # Converte dezenas e trevos para formato individual
    if result['dezenas']:
        for i, dezena in enumerate(result['dezenas'], 1):
            result[f'd{i}'] = dezena
    
    if result['trevos']:
        result['t1'], result['t2'] = result['trevos']
    
    return result


if __name__ == "__main__":
    # Teste básico dos padrões
    test_text = """
    Concurso 123
    Data: 15/06/2023
    Dezenas: 05 12 23 34 45 50
    Trevos: 2 5
    """
    
    result = extract_all_data(test_text)
    print("Teste de extração:")
    for key, value in result.items():
        print(f"  {key}: {value}")