@echo off
setlocal EnableDelayedExpansion

echo ============================================================================
echo                        MILIONARIA AI - INTERFACE WEB
echo ============================================================================
echo.
echo Iniciando interface web do Milionaria AI...
echo.
echo IMPORTANTE:
echo - A interface sera aberta automaticamente no seu navegador
echo - Se nao abrir, acesse manualmente: http://localhost:8501
echo - Para parar o servidor, pressione Ctrl+C neste terminal
echo.
echo ============================================================================
echo.

REM Verificar se o executavel existe
if not exist "dist\MilionariaStreamlit.exe" (
    echo ERRO: Executavel nao encontrado!
    echo.
    echo O arquivo dist\MilionariaStreamlit.exe nao foi encontrado.
    echo Certifique-se de que o executavel foi compilado corretamente.
    echo.
    pause
    exit /b 1
)

echo Iniciando servidor Streamlit...
echo.

REM Aguardar um pouco e abrir o navegador
echo Aguardando servidor inicializar...
timeout /t 3 /nobreak > nul 2>&1

REM Abrir navegador
echo Abrindo navegador...
start "" "http://localhost:8501"

echo.
echo Interface web iniciada com sucesso!
echo.
echo INSTRUCOES DE USO:
echo   1. Configure os parametros na barra lateral
echo   2. Clique em 'Gerar Jogos' para executar o pipeline
echo   3. Visualize os resultados e metricas
echo   4. Exporte os bilhetes em Excel se desejar
echo.
echo Para parar o servidor: Pressione Ctrl+C ou feche esta janela
echo.
echo ============================================================================
echo.

REM Executar o aplicativo
"dist\MilionariaStreamlit.exe"

echo.
echo Servidor encerrado.
pause