#!/usr/bin/env pwsh
# Script de atualização automática pós-sorteio da +Milionária
# Executa: ativação conda + update_db + sanity_checks + logging
# Uso: .\tasks\update_all.ps1

# Configurações
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDate = Get-Date -Format "yyyyMMdd"
$LogFile = Join-Path (Join-Path $ProjectRoot "logs") "update_$LogDate.log"
$NoNewDrawsFile = Join-Path (Join-Path $ProjectRoot "logs") "no_new_draws_count.txt"
$MaxConsecutiveNoNewDraws = 5  # Número máximo de execuções consecutivas sem novos concursos

# Função para logging com timestamp
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry -Encoding UTF8
}

# Função para executar comando com logging
function Invoke-LoggedCommand {
    param([string]$Command, [string]$Description)
    Write-Log "Executando: $Description"
    Write-Log "Comando: $Command" "DEBUG"
    
    try {
        $Output = & cmd /c "$Command 2>&1"
        $ExitCode = $LASTEXITCODE
        
        if ($ExitCode -eq 0) {
            Write-Log "$Description concluido com sucesso"
            Write-Log "Output: $Output" "DEBUG"
            return $Output
        } else {
            Write-Log "Comando falhou com exit code $ExitCode" "ERROR"
            Write-Log "Output: $Output" "ERROR"
            throw "Comando falhou com exit code $ExitCode"
        }
    }
    catch {
        Write-Log "Erro em $Description`: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Função para ler contador de execuções sem novos concursos
function Get-NoNewDrawsCount {
    if (Test-Path $NoNewDrawsFile) {
        try {
            $Count = [int](Get-Content $NoNewDrawsFile -ErrorAction Stop)
            return $Count
        }
        catch {
            Write-Log "Erro ao ler contador, resetando para 0" "WARN"
            return 0
        }
    }
    return 0
}

# Função para incrementar contador de execuções sem novos concursos
function Increment-NoNewDrawsCount {
    $CurrentCount = Get-NoNewDrawsCount
    $NewCount = $CurrentCount + 1
    Set-Content -Path $NoNewDrawsFile -Value $NewCount -Encoding UTF8
    Write-Log "Contador de execuções sem novos concursos: $NewCount"
    return $NewCount
}

# Função para resetar contador de execuções sem novos concursos
function Reset-NoNewDrawsCount {
    Set-Content -Path $NoNewDrawsFile -Value "0" -Encoding UTF8
    Write-Log "Contador de execuções sem novos concursos resetado"
}

# Função para verificar se deve disparar alerta de anomalia
function Test-AnomalyAlert {
    param([int]$Count)
    if ($Count -ge $MaxConsecutiveNoNewDraws) {
        Write-Log "ANOMALIA DETECTADA: $Count execuções consecutivas sem novos concursos (limite: $MaxConsecutiveNoNewDraws)" "ERROR"
        
        # Tentar enviar notificação
        try {
            Write-Log "Tentando enviar notificação de anomalia..."
            $NotifyOutput = Invoke-LoggedCommand "python -m src.utils.notify --type anomaly --message 'Detectadas $Count execuções consecutivas sem novos concursos'" "Notificação de anomalia"
            Write-Log "Notificação enviada: $NotifyOutput"
        }
        catch {
            Write-Log "Falha ao enviar notificação: $($_.Exception.Message)" "ERROR"
        }
        
        return $true
    }
    return $false
}

try {
    # Início do processo
    Write-Log "Iniciando atualizacao automatica da +Milionaria" "INFO"
    Write-Log "Diretorio de trabalho: $ProjectRoot"
    Write-Log "Log salvo em: $LogFile"
    
    # Mudar para diretório do projeto
    Set-Location $ProjectRoot
    Write-Log "Mudando para diretorio: $ProjectRoot"
    
    # Verificar se Python está disponível
    try {
        $PythonVersion = python --version 2>&1
        Write-Log "Python detectado: $PythonVersion"
    }
    catch {
        Write-Log "Python nao encontrado. Verifique a instalacao." "ERROR"
        exit 1
    }
    
    # Executar atualização do banco de dados
    Write-Log "Executando atualizacao do banco de dados"
    $UpdateOutput = Invoke-LoggedCommand "python -m src.update.update_db" "Atualização do banco de dados"
    
    # Verificar se a atualização foi bem-sucedida e gerenciar contador de anomalias
    $HasNewDraws = $false
    $AnomalyDetected = $false
    
    if ($UpdateOutput -match "Verificações de integridade aprovadas!") {
        Write-Log "Atualizacao e validacao concluidas com sucesso"
        # Verificar se houve novos concursos
        if ($UpdateOutput -match "Novos: 0") {
            Write-Log "Nenhum concurso novo encontrado"
            $NoNewCount = Increment-NoNewDrawsCount
            $AnomalyDetected = Test-AnomalyAlert -Count $NoNewCount
        } else {
            Write-Log "Novos concursos encontrados - resetando contador de anomalias"
            Reset-NoNewDrawsCount
            $HasNewDraws = $true
        }
    }
    elseif ($UpdateOutput -match "Nenhum concurso novo encontrado") {
        Write-Log "Nenhum concurso novo - banco ja atualizado"
        $NoNewCount = Increment-NoNewDrawsCount
        $AnomalyDetected = Test-AnomalyAlert -Count $NoNewCount
    }
    else {
        Write-Log "Atualizacao concluida mas status incerto" "WARN"
        # Em caso de incerteza, não incrementar contador
    }
    
    # Executar validação adicional independente
    Write-Log "Executando validacao independente de integridade"
    $ValidateOutput = Invoke-LoggedCommand "python -m src.utils.validate" "Validação de integridade"
    
    # Verificar resultado da validação
    if ($ValidateOutput -match "Todos os checks de integridade passaram!") {
        Write-Log "Validacao independente aprovada"
    }
    else {
        Write-Log "Falha na validacao independente" "ERROR"
        exit 1
    }
    
    # Estatísticas finais
    Write-Log "Coletando estatisticas finais"
    $StatsOutput = Invoke-LoggedCommand "python tasks/get_stats.py" "Coleta de estatísticas"
    
    Write-Log "Atualizacao automatica concluida com sucesso!" "INFO"
    Write-Log "Estatisticas: $StatsOutput"
    
    # Verificar se deve retornar código de erro devido a anomalia
    if ($AnomalyDetected) {
        Write-Log "Retornando codigo de erro devido a anomalia detectada" "ERROR"
        exit 2  # Código específico para anomalia
    }
    
    exit 0
    
}
catch {
    Write-Log "Falha critica na atualizacao automatica: $($_.Exception.Message)" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    
    # Tentar coletar informações de diagnóstico
    try {
        Write-Log "Coletando informacoes de diagnostico..." "INFO"
        $DiagOutput = Invoke-Expression "python tasks/get_stats.py" 2>&1
        Write-Log "Diagnostico: $DiagOutput" "INFO"
    }
    catch {
        Write-Log "Nao foi possivel coletar diagnostico" "ERROR"
    }
    
    exit 1
}
finally {
    $EndTime = Get-Date
    Write-Log "Processo finalizado em: $EndTime"
    Write-Log "Log completo salvo em: $LogFile"
}