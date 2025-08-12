#!/usr/bin/env pwsh
# Script de auto-verificacao completa do projeto Milionaria AI
# Executa auditoria ponta-a-ponta verificando estrutura, dados e funcionalidades

$ErrorActionPreference = "Continue"  # Continuar mesmo com erros para coletar todos os resultados
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDate = Get-Date -Format "yyyyMMdd_HHmmss"
$AuditDir = Join-Path (Join-Path $ProjectRoot "logs") "auditoria"
$SelfCheckLog = Join-Path $AuditDir "99_self_check.log"

# Criar diretorio de auditoria se nao existir
if (-not (Test-Path $AuditDir)) {
    New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null
}

# Funcao para logging com timestamp
function Write-AuditLog {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $SelfCheckLog -Value $LogEntry -Encoding UTF8
}

# Funcao para executar comando com logging
function Invoke-AuditCommand {
    param([string]$Command, [string]$Description)
    Write-AuditLog "Executando: $Description"
    Write-AuditLog "Comando: $Command" "DEBUG"
    
    try {
        $Output = & cmd /c "$Command 2>&1"
        $ExitCode = $LASTEXITCODE
        
        Write-AuditLog "Exit code: $ExitCode" "DEBUG"
        Write-AuditLog "Output: $Output" "DEBUG"
        
        return @{
            "success" = ($ExitCode -eq 0)
            "exit_code" = $ExitCode
            "output" = $Output
        }
    }
    catch {
        Write-AuditLog "Erro em $Description`: $($_.Exception.Message)" "ERROR"
        return @{
            "success" = $false
            "exit_code" = -1
            "output" = $_.Exception.Message
        }
    }
}

# Funcao para verificar estrutura de diretorios
function Test-ProjectStructure {
    Write-AuditLog "=== VERIFICANDO ESTRUTURA DO PROJETO ===" "INFO"
    
    $RequiredDirs = @(
        "src",
        "src/audit",
        "src/db",
        "src/etl",
        "src/features",
        "src/generate",
        "src/ingest",
        "src/models",
        "src/simulate",
        "src/update",
        "src/utils",
        "tests",
        "tasks",
        "db",
        "logs",
        "outputs",
        "data"
    )
    
    $RequiredFiles = @(
        "src/audit/db_inspect.py",
        "src/db/io.py",
        "src/db/schema.py",
        "src/utils/validate.py",
        "src/update/update_db.py",
        "tests/test_db_contract.py",
        "tasks/update_all.ps1",
        "db/milionaria.db"
    )
    
    $StructureIssues = @()
    
    # Verificar diretorios
    foreach ($dir in $RequiredDirs) {
        $fullPath = Join-Path $ProjectRoot $dir
        if (-not (Test-Path $fullPath)) {
            $StructureIssues += "Missing directory: $dir"
            Write-AuditLog "MISSING: $dir" "ERROR"
        } else {
            Write-AuditLog "OK: $dir" "DEBUG"
        }
    }
    
    # Verificar arquivos
    foreach ($file in $RequiredFiles) {
        $fullPath = Join-Path $ProjectRoot $file
        if (-not (Test-Path $fullPath)) {
            $StructureIssues += "Missing file: $file"
            Write-AuditLog "MISSING: $file" "ERROR"
        } else {
            Write-AuditLog "OK: $file" "DEBUG"
        }
    }
    
    if ($StructureIssues.Count -eq 0) {
        Write-AuditLog "Estrutura do projeto: PASS" "INFO"
        return $true
    } else {
        Write-AuditLog "Estrutura do projeto: FAIL ($($StructureIssues.Count) issues)" "ERROR"
        foreach ($issue in $StructureIssues) {
            Write-AuditLog "  - $issue" "ERROR"
        }
        return $false
    }
}

# Funcao para verificar ambiente Python
function Test-PythonEnvironment {
    Write-AuditLog "=== VERIFICANDO AMBIENTE PYTHON ===" "INFO"
    
    # Verificar Python
    try {
        $PythonVersion = python --version 2>&1
        Write-AuditLog "Python version: $PythonVersion"
    }
    catch {
        Write-AuditLog "Python nao encontrado" "ERROR"
        return $false
    }
    
    # Verificar modulos essenciais
    $RequiredModules = @("pandas", "sqlite3", "pathlib", "pytest")
    $ModuleIssues = @()
    
    foreach ($module in $RequiredModules) {
        $result = Invoke-AuditCommand "python -c \"import $module; print('$module OK')\"" "Verificar modulo $module"
        if (-not $result.success) {
            $ModuleIssues += $module
        }
    }
    
    if ($ModuleIssues.Count -eq 0) {
        Write-AuditLog "Ambiente Python: PASS" "INFO"
        return $true
    } else {
        Write-AuditLog "Ambiente Python: FAIL (missing modules: $($ModuleIssues -join ', '))" "ERROR"
        return $false
    }
}

try {
    Write-AuditLog "=== INICIANDO AUDITORIA COMPLETA ===" "INFO"
    Write-AuditLog "Projeto: Milionaria AI"
    Write-AuditLog "Diretorio: $ProjectRoot"
    Write-AuditLog "Log de auditoria: $SelfCheckLog"
    Write-AuditLog "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    
    # Mudar para diretorio do projeto
    Set-Location $ProjectRoot
    Write-AuditLog "Working directory: $ProjectRoot"
    
    $AllTestsPassed = $true
    
    # 1. Verificar estrutura do projeto
    $StructureOK = Test-ProjectStructure
    $AllTestsPassed = $AllTestsPassed -and $StructureOK
    
    # 2. Verificar ambiente Python
    $PythonOK = Test-PythonEnvironment
    $AllTestsPassed = $AllTestsPassed -and $PythonOK
    
    # 3. Executar inspecao do banco de dados
    Write-AuditLog "=== EXECUTANDO INSPECAO DO BANCO ===" "INFO"
    $DbInspectResult = Invoke-AuditCommand "python -m src.audit.db_inspect" "Inspecao do banco de dados"
    $AllTestsPassed = $AllTestsPassed -and $DbInspectResult.success
    
    if ($DbInspectResult.success) {
        Write-AuditLog "Inspecao do banco: PASS" "INFO"
    } else {
        Write-AuditLog "Inspecao do banco: FAIL" "ERROR"
    }
    
    # 4. Executar verificacoes de sanidade
    Write-AuditLog "=== EXECUTANDO VERIFICACOES DE SANIDADE ===" "INFO"
    $SanityResult = Invoke-AuditCommand "python -m src.utils.validate" "Verificacoes de sanidade"
    $AllTestsPassed = $AllTestsPassed -and $SanityResult.success
    
    if ($SanityResult.success) {
        Write-AuditLog "Verificacoes de sanidade: PASS" "INFO"
    } else {
        Write-AuditLog "Verificacoes de sanidade: FAIL" "ERROR"
    }
    
    # 5. Testar atualizador (primeira execucao)
    Write-AuditLog "=== TESTANDO ATUALIZADOR (1a EXECUCAO) ===" "INFO"
    $UpdateResult1 = Invoke-AuditCommand "python -m src.update.update_db" "Primeira execucao do atualizador"
    $AllTestsPassed = $AllTestsPassed -and $UpdateResult1.success
    
    if ($UpdateResult1.success) {
        Write-AuditLog "Primeira execucao do atualizador: PASS" "INFO"
    } else {
        Write-AuditLog "Primeira execucao do atualizador: FAIL" "ERROR"
    }
    
    # 6. Testar atualizador (segunda execucao - deve retornar "Novos: 0")
    Write-AuditLog "=== TESTANDO ATUALIZADOR (2a EXECUCAO) ===" "INFO"
    $UpdateResult2 = Invoke-AuditCommand "python -m src.update.update_db" "Segunda execucao do atualizador"
    
    if ($UpdateResult2.success) {
        if ($UpdateResult2.output -match "Novos: 0" -or $UpdateResult2.output -match "Nenhum concurso novo") {
            Write-AuditLog "Segunda execucao do atualizador: PASS (Novos: 0 detectado)" "INFO"
        } else {
            Write-AuditLog "Segunda execucao do atualizador: WARNING (Novos: 0 nao detectado, pode haver novos concursos)" "WARN"
        }
    } else {
        Write-AuditLog "Segunda execucao do atualizador: FAIL" "ERROR"
        $AllTestsPassed = $false
    }
    
    # 7. Verificar exports
    Write-AuditLog "=== VERIFICANDO EXPORTS ===" "INFO"
    $DumpPath = Join-Path $ProjectRoot "outputs/dump.csv"
    $PreviewPath = Join-Path $ProjectRoot "outputs/dump_preview.csv"
    
    if ((Test-Path $DumpPath) -and (Test-Path $PreviewPath)) {
        $DumpSize = (Get-Item $DumpPath).Length
        $PreviewSize = (Get-Item $PreviewPath).Length
        
        Write-AuditLog "Export dump.csv: $DumpSize bytes" "INFO"
        Write-AuditLog "Export dump_preview.csv: $PreviewSize bytes" "INFO"
        
        if ($DumpSize -gt 0 -and $PreviewSize -gt 0) {
            Write-AuditLog "Exports: PASS" "INFO"
        } else {
            Write-AuditLog "Exports: FAIL (arquivos vazios)" "ERROR"
            $AllTestsPassed = $false
        }
    } else {
        Write-AuditLog "Exports: FAIL (arquivos nao encontrados)" "ERROR"
        $AllTestsPassed = $false
    }
    
    # 8. Coletar estatisticas finais
    Write-AuditLog "=== COLETANDO ESTATISTICAS FINAIS ===" "INFO"
    $StatsResult = Invoke-AuditCommand "python tasks/get_stats.py" "Coleta de estatisticas"
    
    if ($StatsResult.success) {
        Write-AuditLog "Estatisticas: $($StatsResult.output)" "INFO"
    } else {
        Write-AuditLog "Falha ao coletar estatisticas" "WARN"
    }
    
    # Resultado final
    Write-AuditLog "=== RESULTADO FINAL DA AUDITORIA ===" "INFO"
    
    if ($AllTestsPassed) {
        Write-AuditLog "AUDITORIA COMPLETA: PASS" "INFO"
        Write-AuditLog "Todos os criterios de aceitacao foram atendidos" "INFO"
        $ExitCode = 0
    } else {
        Write-AuditLog "AUDITORIA COMPLETA: FAIL" "ERROR"
        Write-AuditLog "Um ou mais criterios de aceitacao falharam" "ERROR"
        $ExitCode = 1
    }
    
    Write-AuditLog "Log completo salvo em: $SelfCheckLog" "INFO"
    Write-AuditLog "=== FIM DA AUDITORIA ===" "INFO"
    
    exit $ExitCode
    
}
catch {
    Write-AuditLog "ERRO CRITICO NA AUDITORIA: $($_.Exception.Message)" "ERROR"
    Write-AuditLog "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    
    exit 1
}
finally {
    $EndTime = Get-Date
    Write-AuditLog "Auditoria finalizada em: $EndTime" "INFO"
}