@echo off
REM Milionária AI - Script de Atualização
REM Este script executa o sistema usando Python diretamente

echo ╔════════════════════════════════════════════════════════════╗
echo ║                    MILIONÁRIA AI                           ║
echo ║              Sistema de Análise da Mega                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar se Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado. Por favor, instale o Python 3.8+
    pause
    exit /b 1
)

REM Mudar para o diretório do script
cd /d "%~dp0"

REM Verificar argumentos
if "%1"=="" (
    echo.
    echo Uso: MilionariaUpdate.bat [--update ^| --import arquivo]
    echo.
    echo Exemplos:
    echo   MilionariaUpdate.bat --update
    echo   MilionariaUpdate.bat --import data/raw/base_275.xlsx
    echo.
    pause
    exit /b 1
)

REM Executar o sistema Python
echo 🚀 Iniciando Milionária AI...
echo.
python milionaria.py %*

REM Verificar resultado
if errorlevel 1 (
    echo.
    echo ❌ Erro durante execução. Verifique os logs em logs/milionaria_cli.log
) else (
    echo.
    echo ✅ Operação concluída com sucesso!
)

echo.
echo Pressione qualquer tecla para sair...
pause >nul