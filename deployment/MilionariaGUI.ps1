#!/usr/bin/env powershell
# ============================================================================
# Milionária-AI GUI - Script de Inicialização PowerShell
# Interface Gráfica Moderna para Windows 11
# ============================================================================

# Configurar codificação UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Função para exibir cabeçalho
function Show-Header {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                           🎯 MILIONÁRIA-AI GUI                              ║" -ForegroundColor Cyan
    Write-Host "║                    Gerador Inteligente de Bilhetes v2.0                     ║" -ForegroundColor Cyan
    Write-Host "║                        Interface Gráfica Moderna                            ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

# Função para exibir mensagens coloridas
function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Função para verificar se um comando existe
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Função principal
function Start-MilionariaGUI {
    try {
        Show-Header
        
        # Verificar se o executável existe
        $exePath = "dist\MilionariaGUI.exe"
        if (Test-Path $exePath) {
            Write-ColorMessage "✅ Executável encontrado: $exePath" "Green"
            Write-ColorMessage "🚀 Iniciando interface gráfica..." "Yellow"
            Write-Host ""
            
            # Executar a interface gráfica
            Start-Process -FilePath $exePath -WindowStyle Normal
            
            Write-ColorMessage "✅ Interface gráfica iniciada com sucesso!" "Green"
            Write-ColorMessage "💡 A janela da aplicação deve aparecer em alguns segundos." "Cyan"
            Write-Host ""
            Write-ColorMessage "Pressione qualquer tecla para fechar este terminal..." "Gray"
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            return
        }
        
        # Se o executável não existe, verificar se o Python está disponível
        Write-ColorMessage "⚠️  Executável não encontrado. Verificando Python..." "Yellow"
        Write-Host ""
        
        if (-not (Test-Command "python")) {
            Write-ColorMessage "❌ Python não encontrado!" "Red"
            Write-Host ""
            Write-ColorMessage "📋 INSTRUÇÕES DE INSTALAÇÃO:" "Cyan"
            Write-ColorMessage "   1. Instale o Python 3.11+ do site oficial: https://python.org" "White"
            Write-ColorMessage "   2. Execute o script install.ps1 para configurar o ambiente" "White"
            Write-ColorMessage "   3. Execute este script novamente" "White"
            Write-Host ""
            Write-ColorMessage "Pressione qualquer tecla para sair..." "Gray"
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        }
        
        Write-ColorMessage "✅ Python encontrado!" "Green"
        
        # Verificar versão do Python
        $pythonVersion = python --version 2>&1
        Write-ColorMessage "📋 Versão: $pythonVersion" "Cyan"
        Write-ColorMessage "🔧 Executando interface gráfica diretamente..." "Yellow"
        Write-Host ""
        
        # Ativar ambiente virtual se existir
        $venvPath = ".venv\Scripts\Activate.ps1"
        if (Test-Path $venvPath) {
            Write-ColorMessage "🔄 Ativando ambiente virtual..." "Yellow"
            & $venvPath
        }
        
        # Verificar se o arquivo GUI existe
        $guiFile = "milionaria_gui.py"
        if (-not (Test-Path $guiFile)) {
            Write-ColorMessage "❌ Arquivo $guiFile não encontrado!" "Red"
            Write-ColorMessage "📁 Certifique-se de estar no diretório correto do projeto." "Yellow"
            Write-Host ""
            Write-ColorMessage "📍 Diretório atual: $(Get-Location)" "Cyan"
            Write-Host ""
            Write-ColorMessage "Pressione qualquer tecla para sair..." "Gray"
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        }
        
        # Verificar dependências básicas
        Write-ColorMessage "🔍 Verificando dependências..." "Yellow"
        $dependencies = @("pandas", "numpy", "polars", "sklearn", "requests", "bs4", "yaml")
        $missingDeps = @()
        
        foreach ($dep in $dependencies) {
            try {
                python -c "import $dep" 2>$null
                if ($LASTEXITCODE -ne 0) {
                    $missingDeps += $dep
                }
            }
            catch {
                $missingDeps += $dep
            }
        }
        
        if ($missingDeps.Count -gt 0) {
            Write-ColorMessage "⚠️  Dependências faltando: $($missingDeps -join ', ')" "Yellow"
            Write-ColorMessage "🔧 Instalando dependências..." "Yellow"
            
            try {
                python -m pip install -r requirements.txt
                if ($LASTEXITCODE -ne 0) {
                    throw "Erro na instalação"
                }
                Write-ColorMessage "✅ Dependências instaladas!" "Green"
            }
            catch {
                Write-ColorMessage "❌ Erro ao instalar dependências!" "Red"
                Write-ColorMessage "💡 Execute manualmente: pip install -r requirements.txt" "Cyan"
            }
        }
        else {
            Write-ColorMessage "✅ Todas as dependências estão instaladas!" "Green"
        }
        
        # Executar a interface gráfica com Python
        Write-Host ""
        Write-ColorMessage "🚀 Iniciando Milionária-AI GUI..." "Green"
        Write-ColorMessage "💡 Aguarde a janela da aplicação aparecer..." "Cyan"
        Write-Host ""
        
        # Executar em processo separado para não bloquear o terminal
        $process = Start-Process -FilePath "python" -ArgumentList $guiFile -PassThru -WindowStyle Hidden
        
        # Aguardar um pouco para verificar se o processo iniciou corretamente
        Start-Sleep -Seconds 2
        
        if ($process.HasExited) {
            Write-ColorMessage "❌ Erro ao executar a interface gráfica!" "Red"
            Write-Host ""
            Write-ColorMessage "🔧 POSSÍVEIS SOLUÇÕES:" "Cyan"
            Write-ColorMessage "   1. Instale as dependências: pip install -r requirements.txt" "White"
            Write-ColorMessage "   2. Execute o script install.ps1" "White"
            Write-ColorMessage "   3. Verifique se todos os módulos estão instalados" "White"
            Write-Host ""
            Write-ColorMessage "📋 DEPENDÊNCIAS NECESSÁRIAS:" "Cyan"
            Write-ColorMessage "   - tkinter (incluído no Python)" "White"
            Write-ColorMessage "   - pandas, numpy, polars" "White"
            Write-ColorMessage "   - scikit-learn" "White"
            Write-ColorMessage "   - requests, beautifulsoup4" "White"
            Write-ColorMessage "   - pyyaml" "White"
            Write-Host ""
            Write-ColorMessage "Pressione qualquer tecla para sair..." "Gray"
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        }
        
        Write-ColorMessage "✅ Interface gráfica iniciada com sucesso!" "Green"
        Write-ColorMessage "💡 A aplicação está rodando em segundo plano." "Cyan"
        Write-ColorMessage "🔄 Para fechar, use a própria interface ou o Gerenciador de Tarefas." "Yellow"
        Write-Host ""
        Write-ColorMessage "Pressione qualquer tecla para fechar este terminal..." "Gray"
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        
    }
    catch {
        Write-ColorMessage "❌ Erro inesperado: $($_.Exception.Message)" "Red"
        Write-Host ""
        Write-ColorMessage "📧 Reporte este erro para suporte técnico." "Yellow"
        Write-Host ""
        Write-ColorMessage "Pressione qualquer tecla para sair..." "Gray"
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

# Verificar política de execução
if ((Get-ExecutionPolicy) -eq "Restricted") {
    Write-ColorMessage "⚠️  Política de execução restrita detectada." "Yellow"
    Write-ColorMessage "🔧 Execute: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" "Cyan"
    Write-Host ""
}

# Executar função principal
Start-MilionariaGUI