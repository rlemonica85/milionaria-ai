# Makefile para Milionária AI
# Facilita tarefas comuns de desenvolvimento e instalação

.PHONY: help install install-dev test clean build run-web run-cli update lint format check-format type-check security-check docs

# Configurações
PYTHON := python
PIP := pip
PYTEST := pytest
BLACK := black
FLAKE8 := flake8
MYPY := mypy
PYINSTALLER := pyinstaller
STREAMLIT := streamlit

# Cores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Ajuda padrão
help: ## Mostra esta mensagem de ajuda
	@echo "$(BLUE)Milionária AI - Comandos Disponíveis$(NC)"
	@echo "$(BLUE)====================================$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Instalação
install: ## Instala o projeto e dependências
	@echo "$(BLUE)Instalando Milionária AI...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	playwright install
	$(PYTHON) -c "from src.db.schema import ensure_schema; ensure_schema()"
	@echo "$(GREEN)✓ Instalação concluída!$(NC)"

install-dev: ## Instala dependências de desenvolvimento
	@echo "$(BLUE)Instalando dependências de desenvolvimento...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	playwright install
	$(PYTHON) -c "from src.db.schema import ensure_schema; ensure_schema()"
	@echo "$(GREEN)✓ Instalação de desenvolvimento concluída!$(NC)"

install-gpu: ## Instala com suporte GPU
	@echo "$(BLUE)Instalando com suporte GPU...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[gpu]"
	playwright install
	@echo "$(GREEN)✓ Instalação GPU concluída!$(NC)"

# Testes
test: ## Executa todos os testes
	@echo "$(BLUE)Executando testes...$(NC)"
	$(PYTEST) tests/ -v

test-cov: ## Executa testes com cobertura
	@echo "$(BLUE)Executando testes com cobertura...$(NC)"
	$(PYTEST) tests/ -v --cov=src --cov-report=html --cov-report=term

test-fast: ## Executa apenas testes rápidos
	@echo "$(BLUE)Executando testes rápidos...$(NC)"
	$(PYTEST) tests/ -v -m "not slow"

test-integration: ## Executa testes de integração
	@echo "$(BLUE)Executando testes de integração...$(NC)"
	$(PYTEST) tests/ -v -m "integration"

# Qualidade de código
lint: ## Executa linting (flake8)
	@echo "$(BLUE)Executando linting...$(NC)"
	$(FLAKE8) src/ tests/

format: ## Formata código com black
	@echo "$(BLUE)Formatando código...$(NC)"
	$(BLACK) src/ tests/

check-format: ## Verifica formatação sem alterar
	@echo "$(BLUE)Verificando formatação...$(NC)"
	$(BLACK) --check src/ tests/

type-check: ## Verifica tipos com mypy
	@echo "$(BLUE)Verificando tipos...$(NC)"
	$(MYPY) src/

security-check: ## Verifica vulnerabilidades de segurança
	@echo "$(BLUE)Verificando segurança...$(NC)"
	$(PIP) install bandit safety
	bandit -r src/
	safety check

check-all: lint check-format type-check ## Executa todas as verificações
	@echo "$(GREEN)✓ Todas as verificações concluídas!$(NC)"

# Execução
run-web: ## Inicia interface web (Streamlit)
	@echo "$(BLUE)Iniciando interface web...$(NC)"
	$(STREAMLIT) run app_streamlit.py

run-cli: ## Executa interface de linha de comando
	@echo "$(BLUE)Executando CLI...$(NC)"
	$(PYTHON) milionaria.py --help

update: ## Atualiza dados do banco
	@echo "$(BLUE)Atualizando dados...$(NC)"
	$(PYTHON) -m src.update.update_db

collect: ## Coleta dados iniciais
	@echo "$(BLUE)Coletando dados iniciais...$(NC)"
	$(PYTHON) -m src.cli.app --collect

process: ## Processa dados coletados
	@echo "$(BLUE)Processando dados...$(NC)"
	$(PYTHON) -m src.cli.app --process

# Build e distribuição
build: ## Gera executável com PyInstaller
	@echo "$(BLUE)Gerando executável...$(NC)"
	$(PYINSTALLER) milionaria.spec
	@echo "$(GREEN)✓ Executável gerado em dist/$(NC)"

build-clean: clean build ## Limpa e gera executável

package: ## Cria pacote Python
	@echo "$(BLUE)Criando pacote Python...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Pacote criado em dist/$(NC)"

# Limpeza
clean: ## Remove arquivos temporários e build
	@echo "$(BLUE)Limpando arquivos temporários...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "$(GREEN)✓ Limpeza concluída!$(NC)"

clean-logs: ## Remove logs antigos
	@echo "$(BLUE)Limpando logs...$(NC)"
	find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Logs antigos removidos!$(NC)"

clean-all: clean clean-logs ## Remove tudo (arquivos temporários e logs)

# Desenvolvimento
dev-setup: install-dev ## Configura ambiente de desenvolvimento
	@echo "$(BLUE)Configurando ambiente de desenvolvimento...$(NC)"
	pre-commit install
	@echo "$(GREEN)✓ Ambiente de desenvolvimento configurado!$(NC)"

dev-test: ## Executa testes em modo de desenvolvimento
	@echo "$(BLUE)Executando testes em modo desenvolvimento...$(NC)"
	$(PYTEST) tests/ -v --tb=short -x

dev-watch: ## Executa testes automaticamente ao salvar arquivos
	@echo "$(BLUE)Monitorando arquivos para testes automáticos...$(NC)"
	$(PYTEST) tests/ -v --tb=short -f

# Banco de dados
db-reset: ## Reseta banco de dados
	@echo "$(YELLOW)⚠ Resetando banco de dados...$(NC)"
	rm -f db/milionaria.db
	$(PYTHON) -c "from src.db.schema import ensure_schema; ensure_schema()"
	@echo "$(GREEN)✓ Banco de dados resetado!$(NC)"

db-backup: ## Faz backup do banco de dados
	@echo "$(BLUE)Fazendo backup do banco...$(NC)"
	cp db/milionaria.db db/milionaria_backup_$(shell date +%Y%m%d_%H%M%S).db
	@echo "$(GREEN)✓ Backup criado!$(NC)"

db-inspect: ## Inspeciona banco de dados
	@echo "$(BLUE)Inspecionando banco de dados...$(NC)"
	$(PYTHON) -m src.audit.db_inspect

# Documentação
docs: ## Gera documentação
	@echo "$(BLUE)Gerando documentação...$(NC)"
	@echo "$(YELLOW)Documentação disponível em README.md e INSTALL.md$(NC)"

# Monitoramento
status: ## Mostra status do sistema
	@echo "$(BLUE)Status do Sistema Milionária AI$(NC)"
	@echo "$(BLUE)==============================$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Pip: $$($(PIP) --version)"
	@echo "Banco: $$(test -f db/milionaria.db && echo 'Existe' || echo 'Não encontrado')"
	@echo "Logs: $$(ls -la logs/ | wc -l) arquivos"
	@echo "Outputs: $$(ls -la outputs/ | wc -l) arquivos"

# Utilitários
requirements: ## Atualiza requirements.txt
	@echo "$(BLUE)Atualizando requirements.txt...$(NC)"
	$(PIP) freeze > requirements.txt
	@echo "$(GREEN)✓ Requirements atualizados!$(NC)"

upgrade: ## Atualiza todas as dependências
	@echo "$(BLUE)Atualizando dependências...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements.txt
	@echo "$(GREEN)✓ Dependências atualizadas!$(NC)"

# Comandos compostos
full-check: clean install-dev test check-all ## Instalação completa + testes + verificações
	@echo "$(GREEN)✓ Verificação completa concluída!$(NC)"

quick-start: install run-web ## Instalação rápida + interface web

release: clean test check-all build ## Prepara release (testes + build)
	@echo "$(GREEN)✓ Release preparado em dist/$(NC)"

# Informações
info: ## Mostra informações do projeto
	@echo "$(BLUE)Informações do Projeto$(NC)"
	@echo "$(BLUE)=====================$(NC)"
	@echo "Nome: Milionária AI"
	@echo "Versão: 1.0.0"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Diretório: $$(pwd)"
	@echo "Arquivos Python: $$(find src/ -name '*.py' | wc -l)"
	@echo "Testes: $$(find tests/ -name 'test_*.py' | wc -l)"
	@echo "Linhas de código: $$(find src/ -name '*.py' -exec wc -l {} + | tail -1)"