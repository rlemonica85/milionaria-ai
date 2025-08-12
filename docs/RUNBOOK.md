# 🚨 RUNBOOK - Procedimentos de Emergência

## 📋 Índice

1. [Seletor Mudou](#-seletor-mudou)
2. [Sem Concursos Novos](#-sem-concursos-novos)
3. [Divergência Entre Fontes](#-divergência-entre-fontes)
4. [Banco Corrompido](#-banco-corrompido)
5. [Modo Diagnóstico](#-modo-diagnóstico)
6. [Comandos de Emergência](#-comandos-de-emergência)
7. [Logs e Monitoramento](#-logs-e-monitoramento)

---

## 🔧 Seletor Mudou

### Sintomas
- Erro "Element not found" no Playwright
- Timeout durante scraping
- Dados não extraídos corretamente

### Diagnóstico
```bash
# 1. Executar modo diagnóstico
python -c "from src.update.fetch_caixa import CaixaFetcher; import asyncio; asyncio.run(CaixaFetcher().debug_mode())"

# 2. Verificar logs de erro
tail -f logs/update_$(date +%Y%m%d).log
```

### Correção

#### Passo 1: Identificar seletores quebrados
```bash
# Verificar arquivo de seletores
cat src/utils/caixa_selectors.py
```

#### Passo 2: Atualizar seletores
Editar `src/utils/caixa_selectors.py`:

```python
# Exemplo de atualização
CLASS_SELECTORS = {
    'concurso_number': '.numero-concurso-novo',  # Atualizar aqui
    'result_table': 'table.resultado-novo',      # E aqui
    # ...
}
```

#### Passo 3: Testar correção
```bash
# Testar com um concurso específico
python -c "from src.update.fetch_caixa import CaixaFetcher; import asyncio; asyncio.run(CaixaFetcher().fetch_single(275))"
```

#### Passo 4: Validar em produção
```bash
# Executar atualização completa
python milionaria.py --update
```

---

## ⏰ Sem Concursos Novos

### Sintomas
- "Nenhum concurso novo encontrado"
- Último concurso não atualizado há dias

### Diagnóstico
```bash
# Verificar último concurso no banco
python -c "from src.db.io import read_max_concurso; print(f'Último concurso: {read_max_concurso()}')"

# Verificar site da Caixa manualmente
echo "Verificar: https://loterias.caixa.gov.br/Paginas/Mais-Milionaria.aspx"
```

### Quando Reexecutar

#### Cenário 1: Sorteio ainda não ocorreu
```bash
# Aguardar até próximo sorteio (quartas e sábados, 20h)
# Reexecutar após 21h do dia do sorteio
crontab -e
# Adicionar: 0 21 * * 3,6 /path/to/milionaria.py --update
```

#### Cenário 2: Falha temporária
```bash
# Reexecutar imediatamente
python milionaria.py --update

# Se falhar, aguardar 30 minutos e tentar novamente
sleep 1800 && python milionaria.py --update
```

#### Cenário 3: Problema no site da Caixa
```bash
# Ativar modo fallback
python -c "from src.update.fallback_update import run_fallback; run_fallback()"
```

---

## ⚠️ Divergência Entre Fontes

### Sintomas
- Dados diferentes entre Caixa e APIs externas
- Alertas de inconsistência nos logs

### Procedimento PENDING REVIEW

#### Passo 1: Coletar evidências
```bash
# Salvar dados da Caixa
python -c "from src.update.caixa_provider import CaixaProvider; import asyncio; data = asyncio.run(CaixaProvider().fetch_latest()); print(data)" > evidence_caixa.json

# Salvar dados da API externa
python -c "from src.update.external_api_provider import ExternalAPIProvider; import asyncio; data = asyncio.run(ExternalAPIProvider().fetch_latest()); print(data)" > evidence_api.json
```

#### Passo 2: Comparar dados
```bash
# Executar comparação
python -c "
from src.utils.validate import compare_sources
result = compare_sources('evidence_caixa.json', 'evidence_api.json')
print(f'Divergências encontradas: {result}')
"
```

#### Passo 3: Marcar para revisão
```bash
# Criar ticket de revisão
echo "PENDING REVIEW: Divergência detectada em $(date)" >> logs/pending_reviews.log
echo "Arquivos: evidence_caixa.json, evidence_api.json" >> logs/pending_reviews.log

# Pausar atualizações automáticas
touch .maintenance_mode
```

#### Passo 4: Resolução manual
```bash
# Após análise manual, escolher fonte confiável
# Exemplo: usar dados da Caixa
python -c "from src.db.io import upsert_rows; import pandas as pd; df = pd.read_json('evidence_caixa.json'); upsert_rows(df)"

# Remover modo manutenção
rm .maintenance_mode
```

---

## 💾 Banco Corrompido

### Sintomas
- Erro "database is locked"
- Dados inconsistentes
- Falha ao conectar no SQLite

### Restore a partir da planilha

#### Passo 1: Backup do banco corrompido
```bash
# Fazer backup do banco atual
cp db/milionaria.db db/milionaria_corrupted_$(date +%Y%m%d_%H%M%S).db
```

#### Passo 2: Remover banco corrompido
```bash
# Remover banco corrompido
rm db/milionaria.db
```

#### Passo 3: Restaurar da planilha
```bash
# Importar dados da planilha base
python milionaria.py --import data/raw/base_275.xlsx
```

#### Passo 4: Reprocessar dados
```bash
# Executar atualização completa
python milionaria.py --update

# Verificar integridade
python -c "from src.utils.validate import sanity_checks; sanity_checks()"
```

#### Passo 5: Validar restauração
```bash
# Verificar contagem de registros
python -c "from src.db.io import read_max_concurso; print(f'Registros restaurados até concurso: {read_max_concurso()}')"

# Executar testes de integridade
pytest tests/test_db.py -v
```

---

## 🔍 Modo Diagnóstico

### Ativação do modo debug

#### Salvar HTMLs e Screenshots
```bash
# Criar diretório de diagnóstico
mkdir -p logs/debug/$(date +%Y%m%d_%H%M%S)

# Executar com modo debug
python -c "
import asyncio
from src.update.fetch_caixa import CaixaFetcher

async def debug_session():
    async with CaixaFetcher(debug_mode=True) as fetcher:
        await fetcher.debug_capture_all()
        
asyncio.run(debug_session())
"
```

#### Configurar Playwright para debug
Editar `src/update/fetch_caixa.py`:

```python
# Adicionar no método __aenter__
if self.debug_mode:
    self.context = await self.browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        record_video_dir='logs/debug/videos/',
        record_har_path='logs/debug/network.har'
    )
```

#### Capturar evidências específicas
```bash
# Capturar página específica
python -c "
import asyncio
from playwright.async_api import async_playwright

async def capture_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://loterias.caixa.gov.br/Paginas/Mais-Milionaria.aspx')
        await page.screenshot(path='logs/debug/caixa_page.png')
        html = await page.content()
        with open('logs/debug/caixa_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        await browser.close()
        
asyncio.run(capture_page())
"
```

---

## 🚨 Comandos de Emergência

### Parada de emergência
```bash
# Parar todos os processos
pkill -f "python.*milionaria"
pkill -f "streamlit.*app_streamlit"

# Ativar modo manutenção
touch .maintenance_mode
echo "Sistema em manutenção desde $(date)" > .maintenance_mode
```

### Reinício rápido
```bash
# Remover modo manutenção
rm -f .maintenance_mode

# Verificar integridade básica
python -c "from src.utils.validate import basic_checks; basic_checks()"

# Reiniciar aplicação
streamlit run app_streamlit.py &
```

### Rollback de dados
```bash
# Listar backups disponíveis
ls -la db/milionaria_backup_*.db

# Restaurar backup específico
cp db/milionaria_backup_YYYYMMDD_HHMMSS.db db/milionaria.db

# Verificar restauração
python -c "from src.db.io import read_max_concurso; print(f'Rollback para concurso: {read_max_concurso()}')"
```

---

## 📊 Logs e Monitoramento

### Localização dos logs
- **Aplicação principal**: `logs/milionaria_cli.log`
- **Streamlit**: `logs/streamlit_debug.log`
- **Atualizações**: `logs/update_YYYYMMDD.log`
- **Métricas**: `logs/metrics.csv`
- **Fallback**: `logs/fallback/`
- **HTMLs debug**: `logs/html/`

### Monitoramento em tempo real
```bash
# Monitorar logs principais
tail -f logs/milionaria_cli.log

# Monitorar métricas
watch -n 5 "tail -5 logs/metrics.csv"

# Verificar status do sistema
python -c "from src.utils.validate import system_health; system_health()"
```

### Alertas automáticos
```bash
# Configurar alerta para erros críticos
echo '*/5 * * * * grep -q "ERROR\|CRITICAL" logs/milionaria_cli.log && echo "ALERTA: Erro crítico detectado" | mail -s "Milionária AI - Erro" admin@domain.com' | crontab -
```

---

## 📞 Contatos de Emergência

- **Desenvolvedor Principal**: [Inserir contato]
- **Administrador do Sistema**: [Inserir contato]
- **Suporte Técnico**: [Inserir contato]

---

## 📝 Histórico de Incidentes

### Template para documentar incidentes
```
DATA: YYYY-MM-DD HH:MM
TIPO: [Seletor/Dados/Banco/Rede]
DESCRIÇÃO: [Descrição do problema]
SOLUÇÃO: [Passos executados]
TEMPO RESOLUÇÃO: [Tempo total]
PREVENÇÃO: [Medidas preventivas]
---
```

### Localização do histórico
- Arquivo: `logs/incident_history.log`
- Backup: `logs/incidents_backup/`

---

*Última atualização: $(date +"%Y-%m-%d %H:%M:%S")*

*Este runbook deve ser atualizado após cada incidente para melhorar os procedimentos.*