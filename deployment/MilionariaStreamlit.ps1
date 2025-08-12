# Milionária AI - Interface Web Streamlit
# Script PowerShell para executar a interface web

# Configurar encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Função para exibir mensagens coloridas
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }

# Cabeçalho
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host "                        MILIONÁRIA AI - INTERFACE WEB" -ForegroundColor Blue
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host ""
Write-Info "Iniciando interface web do Milionária AI..."
Write-Host ""
Write-Warning "IMPORTANTE:"
Write-Host "- A interface será aberta automaticamente no seu navegador"
Write-Host "- Se não abrir, acesse manualmente: http://localhost:8501"
Write-Host "- Para parar o servidor, pressione Ctrl+C neste terminal"
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host ""

try {
    # Verificar se o executável existe
    $exePath = "dist\MilionariaStreamlit.exe"
    if (-not (Test-Path $exePath)) {
        Write-Error "❌ ERRO: Executável não encontrado!"
        Write-Host ""
        Write-Host "O arquivo $exePath não foi encontrado."
        Write-Host "Certifique-se de que o executável foi compilado corretamente."
        Write-Host ""
        Read-Host "Pressione Enter para sair"
        exit 1
    }
    
    Write-Success "🚀 Iniciando servidor Streamlit..."
    Write-Host ""
    
    # Aguardar um pouco e abrir o navegador
    Write-Info "⏳ Aguardando servidor inicializar..."
    Start-Sleep -Seconds 3
    
    # Abrir navegador
    Write-Info "🌐 Abrindo navegador..."
    Start-Process "http://localhost:8501"
    
    Write-Host ""
    Write-Success "✅ Interface web iniciada com sucesso!"
    Write-Host ""
    Write-Info "📋 INSTRUÇÕES DE USO:"
    Write-Host "  1. Configure os parâmetros na barra lateral"
    Write-Host "  2. Clique em 'Gerar Jogos' para executar o pipeline"
    Write-Host "  3. Visualize os resultados e métricas"
    Write-Host "  4. Exporte os bilhetes em Excel se desejar"
    Write-Host ""
    Write-Warning "🛑 Para parar o servidor: Pressione Ctrl+C ou feche esta janela"
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Blue
    Write-Host ""
    
    # Executar o aplicativo
    & $exePath
    
} catch {
    Write-Error "❌ Erro ao executar o aplicativo: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "Detalhes do erro:"
    Write-Host $_.Exception.ToString()
    Write-Host ""
} finally {
    Write-Host ""
    Write-Info "🛑 Servidor encerrado."
    Read-Host "Pressione Enter para sair"
}