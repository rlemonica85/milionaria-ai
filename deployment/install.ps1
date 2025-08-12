# Instalador PowerShell para Milionária AI
# Execução: powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [switch]$SkipPlaywright,
    [switch]$DevMode,
    [switch]$Help
)

if ($Help) {
    Write-Output "Instalador do Sistema Milionária AI"
    Write-Output ""
    Write-Output "Uso: powershell -ExecutionPolicy Bypass -File install.ps1 [opções]"
    Write-Output ""
    Write-Output "Opções:"
    Write-Output "  -SkipPlaywright    Pula a instalação do Playwright"
    Write-Output "  -DevMode          Instala dependências de desenvolvimento"
    Write-Output "  -Help             Mostra esta ajuda"
    Write-Output ""
    exit 0
}

# Funções auxiliares
function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

# Banner
Write-Output ""
Write-Output "============================================================================"
Write-Output "                    INSTALADOR MILIONÁRIA AI v2.0"
Write-Output "============================================================================"
Write-Output ""
Write-Output "Este script irá:"
Write-Output "  1. Verificar instalação do Python 3.11+"
Write-Output "  2. Atualizar pip"
Write-Output "  3. Instalar dependências Python"
if (-not $SkipPlaywright) {
    Write-Output "  4. Configurar Playwright"
} else {
    Write-Output "  4. Pular configuração do Playwright"
}
Write-Output "  5. Criar estrutura de diretórios"
Write-Output "  6. Configurar banco de dados"
Write-Output ""
Read-Host "Pressione Enter para continuar ou Ctrl+C para cancelar"

try {
    # Verificar se Python está instalado
    Write-Info "[1/6] Verificando instalação do Python..."
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "ERRO: Python não encontrado!"
        Write-Output "Por favor, instale Python 3.11 ou superior de https://python.org"
        exit 1
    }
    
    # Verificar versão do Python
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Error "ERRO: Python 3.11+ é necessário. Versão encontrada: $pythonVersion"
            exit 1
        }
    }
    Write-Success "✓ $pythonVersion encontrado"
    
    # Atualizar pip
    Write-Info "[2/6] Atualizando pip..."
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao atualizar pip"
    }
    Write-Success "✓ pip atualizado"
    
    # Instalar dependências
    Write-Info "[3/6] Instalando dependências Python..."
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao instalar dependências do requirements.txt"
        }
    } else {
        Write-Warning "Arquivo requirements.txt não encontrado, instalando dependências básicas..."
        pip install pandas polars pydantic sqlalchemy aiosqlite openpyxl playwright lxml tenacity dateparser pytest pyinstaller streamlit
    }
    
    # Instalar dependências de desenvolvimento se solicitado
    if ($DevMode) {
        Write-Info "Instalando dependências de desenvolvimento..."
        pip install pytest-asyncio pytest-cov black flake8 mypy
    }
    Write-Success "✓ Dependências instaladas"
    
    # Configurar Playwright
    if (-not $SkipPlaywright) {
        Write-Info "[4/6] Configurando Playwright..."
        python -m playwright install
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "AVISO: Falha ao instalar navegadores do Playwright"
            Write-Output "Você pode instalar manualmente com: python -m playwright install"
        } else {
            Write-Success "✓ Playwright configurado"
        }
    } else {
        Write-Info "[4/6] Pulando configuração do Playwright..."
    }
    
    # Criar estrutura de diretórios
    Write-Info "[5/6] Criando estrutura de diretórios..."
    $directories = @(
        "logs",
        "logs\fallback",
        "logs\html",
        "logs\auditoria",
        "outputs",
        "data\raw",
        "data\processed",
        "db"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Output "  ✓ Criado: $dir"
        }
    }
    Write-Success "✓ Estrutura de diretórios criada"
    
    # Configurar banco de dados inicial
    Write-Info "[6/6] Configurando banco de dados..."
    $dbResult = python -c "from src.db.schema import ensure_schema; ensure_schema(); print('Banco de dados configurado com sucesso')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Banco de dados configurado"
    } else {
        Write-Warning "AVISO: Falha ao criar esquema do banco de dados"
        Write-Output "Você pode criar manualmente executando o sistema pela primeira vez"
    }
    
    # Executar testes básicos
    Write-Info "\nExecutando testes de verificação..."
    
    $tests = @(
        @{"Test" = "import src"; "Description" = "Importação do módulo src"},
        @{"Test" = "from src.db.schema import get_engine"; "Description" = "Conexão com banco"},
        @{"Test" = "from playwright.sync_api import sync_playwright"; "Description" = "Playwright"}
    )
    
    foreach ($test in $tests) {
        $testResult = python -c $test.Test 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  ✓ $($test.Description) OK"
        } else {
            Write-Warning "  ⚠ $($test.Description) FALHOU"
        }
    }
    
    # Sucesso
    Write-Output ""
    Write-Success "============================================================================"
    Write-Success "                        INSTALAÇÃO CONCLUÍDA!"
    Write-Success "============================================================================"
    Write-Output ""
    Write-Output "O sistema Milionária AI foi instalado com sucesso!"
    Write-Output ""
    Write-Info "Para usar o sistema:"
    Write-Output "  1. Interface web: streamlit run app_streamlit.py"
    Write-Output "  2. Linha de comando: python milionaria.py"
    Write-Output "  3. Atualização automática: python -m src.update.update_db"
    Write-Output ""
    Write-Info "Comandos úteis:"
    Write-Output "  • Executar testes: pytest tests/ -v"
    Write-Output "  • Gerar executável: pyinstaller milionaria.spec"
    Write-Output "  • Atualizar dados: python -m src.cli.app --collect"
    Write-Output ""
    Write-Output "Para mais informações, consulte o README.md"
    Write-Output ""
    
} catch {
    Write-Error "\nERRO DURANTE A INSTALAÇÃO: $($_.Exception.Message)"
    Write-Output "\nPara suporte, verifique:"
    Write-Output "  • Se Python 3.11+ está instalado corretamente"
    Write-Output "  • Se há conexão com a internet"
    Write-Output "  • Se há permissões de escrita no diretório"
    Write-Output "  • Os logs de erro acima"
    exit 1
}

Read-Host "\nPressione Enter para finalizar"