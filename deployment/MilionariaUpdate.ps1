# Milionaria AI - Script de Atualizacao PowerShell

Write-Host "Milionaria AI - Sistema de Analise da Mega" -ForegroundColor Cyan
Write-Host "" 

# Verificar se o ambiente virtual existe
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Ambiente virtual nao encontrado. Execute install.ps1 primeiro." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Verificar argumentos
if ($args.Count -eq 0) {
    Write-Host "Uso: .\MilionariaUpdate.ps1 --update" -ForegroundColor Yellow
    Write-Host "Exemplo: .\MilionariaUpdate.ps1 --update" -ForegroundColor Gray
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Executar o sistema
Write-Host "Iniciando Milionaria AI..." -ForegroundColor Green
Write-Host ""

try {
    & ".venv\Scripts\python.exe" "milionaria.py" @args
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Operacao concluida com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "Erro durante execucao." -ForegroundColor Red
    }
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

Read-Host "Pressione Enter para sair"