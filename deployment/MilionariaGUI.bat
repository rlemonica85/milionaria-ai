@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================================
REM Milionária-AI GUI - Script de Inicialização
REM Interface Gráfica Moderna para Windows 11
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                           🎯 MILIONÁRIA-AI GUI                              ║
echo ║                    Gerador Inteligente de Bilhetes v2.0                     ║
echo ║                        Interface Gráfica Moderna                            ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

REM Verificar se o executável existe
if exist "dist\MilionariaGUI.exe" (
    echo ✅ Executável encontrado: dist\MilionariaGUI.exe
    echo 🚀 Iniciando interface gráfica...
    echo.
    
    REM Executar a interface gráfica
    start "" "dist\MilionariaGUI.exe"
    
    echo ✅ Interface gráfica iniciada com sucesso!
    echo 💡 A janela da aplicação deve aparecer em alguns segundos.
    echo.
    echo Pressione qualquer tecla para fechar este terminal...
    pause >nul
    exit /b 0
)

REM Se o executável não existe, verificar se o Python está disponível
echo ⚠️  Executável não encontrado. Verificando Python...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo 📋 INSTRUÇÕES DE INSTALAÇÃO:
    echo    1. Instale o Python 3.11+ do site oficial: https://python.org
    echo    2. Execute o script install.bat para configurar o ambiente
    echo    3. Execute este script novamente
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
    exit /b 1
)

echo ✅ Python encontrado!
echo 🔧 Executando interface gráfica diretamente...
echo.

REM Ativar ambiente virtual se existir
if exist ".venv\Scripts\activate.bat" (
    echo 🔄 Ativando ambiente virtual...
    call ".venv\Scripts\activate.bat"
)

REM Verificar se o arquivo GUI existe
if not exist "milionaria_gui.py" (
    echo ❌ Arquivo milionaria_gui.py não encontrado!
    echo 📁 Certifique-se de estar no diretório correto do projeto.
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
    exit /b 1
)

REM Executar a interface gráfica com Python
echo 🚀 Iniciando Milionária-AI GUI...
echo.
python milionaria_gui.py

REM Verificar se houve erro
if errorlevel 1 (
    echo.
    echo ❌ Erro ao executar a interface gráfica!
    echo.
    echo 🔧 POSSÍVEIS SOLUÇÕES:
    echo    1. Instale as dependências: pip install -r requirements.txt
    echo    2. Execute o script install.bat
    echo    3. Verifique se todos os módulos estão instalados
    echo.
    echo 📋 DEPENDÊNCIAS NECESSÁRIAS:
    echo    - tkinter (incluído no Python)
    echo    - pandas
    echo    - numpy
    echo    - polars
    echo    - scikit-learn
    echo    - requests
    echo    - beautifulsoup4
    echo    - pyyaml
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
    exit /b 1
)

echo.
echo ✅ Interface gráfica encerrada normalmente.
echo 💡 Obrigado por usar o Milionária-AI!
echo.
echo Pressione qualquer tecla para sair...

pause >nul