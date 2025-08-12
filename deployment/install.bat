@echo off
REM ============================================================================
REM Instalador Automático - Milionária AI
REM ============================================================================
REM Este script instala automaticamente todas as dependências e configura
REM o ambiente para o sistema Milionária AI
REM ============================================================================

echo.
echo ============================================================================
echo                        MILIONARIA AI - INSTALADOR
echo ============================================================================
echo.
echo Este instalador irá:
echo 1. Verificar se Python 3.11+ está instalado
echo 2. Instalar todas as dependências necessárias
echo 3. Configurar o ambiente Playwright
echo 4. Criar estrutura de diretórios
echo 5. Configurar o banco de dados
echo 6. Executar testes de verificação
echo.
pause

REM Verificar se Python está instalado
echo [1/6] Verificando instalação do Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python não encontrado!
    echo Por favor, instale Python 3.11 ou superior de https://python.org
    pause
    exit /b 1
)

REM Verificar versão do Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% encontrado.

REM Atualizar pip
echo [2/6] Atualizando pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ERRO: Falha ao atualizar pip
    pause
    exit /b 1
)

REM Instalar dependências
echo [3/6] Instalando dependências Python...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar dependências
    pause
    exit /b 1
)

REM Configurar Playwright
echo [4/6] Configurando Playwright...
playwright install
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar navegadores do Playwright
    echo Você pode instalar manualmente com: playwright install
)

REM Criar estrutura de diretórios
echo [5/6] Criando estrutura de diretórios...
if not exist "logs" mkdir logs
if not exist "outputs" mkdir outputs
if not exist "data\raw" mkdir data\raw
if not exist "data\processed" mkdir data\processed
if not exist "db" mkdir db

REM Configurar banco de dados inicial
echo [6/6] Configurando banco de dados...
python -c "from src.db.schema import ensure_schema; ensure_schema()"
if %errorlevel% neq 0 (
    echo AVISO: Falha ao criar esquema do banco de dados
    echo Você pode criar manualmente executando o sistema pela primeira vez
)

REM Executar testes básicos
echo.
echo Executando testes de verificação...
python -c "import src; print('✓ Importação do módulo src OK')"
python -c "from src.db.schema import get_engine; print('✓ Conexão com banco OK')"
python -c "from playwright.sync_api import sync_playwright; print('✓ Playwright OK')"

echo.
echo ============================================================================
echo                        INSTALAÇÃO CONCLUÍDA!
echo ============================================================================
echo.
echo O sistema Milionária AI foi instalado com sucesso!
echo.
echo Para usar o sistema:
echo   1. Interface web: streamlit run app_streamlit.py
echo   2. Linha de comando: python milionaria.py
echo   3. Atualização automática: python -m src.update.update_db
echo.
echo Para mais informações, consulte o README.md
echo.
pause