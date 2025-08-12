# Milionária AI

Projeto para coleta, análise e predição de resultados da loteria +Milionária usando inteligência artificial.

## Descrição

Este projeto automatiza a coleta de dados históricos da +Milionária, processa os dados em um banco SQLite e utiliza técnicas de machine learning para análise e simulação de resultados.

## Executável MilionariaUpdate

O projeto inclui um executável standalone (`MilionariaUpdate.exe`) que permite operações de importação e atualização sem necessidade de instalação do Python.

### Uso do Executável

```bash
# Importar dados iniciais de arquivo Excel
MilionariaUpdate.exe --import data/raw/base_275.xlsx

# Atualizar dados via web scraping
MilionariaUpdate.exe --update

# Exibir ajuda
MilionariaUpdate.exe --help
```

### Geração do Executável

```bash
# Instalar PyInstaller
pip install pyinstaller

# Gerar executável
pyinstaller milionaria.spec

# O executável será criado em dist/MilionariaUpdate.exe
```

## Estrutura do Projeto

```
milionaria-ai/
├── data/
│   ├── raw/          # Dados brutos coletados
│   └── processed/    # Dados processados
├── db/               # Banco de dados SQLite
├── src/
│   ├── db/           # Módulos de banco de dados
│   ├── ingest/       # Coleta de dados
│   ├── update/       # Atualização automática
│   ├── utils/        # Utilitários gerais
│   ├── etl/          # Extract, Transform, Load
│   ├── features/     # Engenharia de features
│   ├── models/       # Modelos de ML
│   ├── simulate/     # Simulações
│   ├── generate/     # Geração de números
│   └── cli/          # Interface de linha de comando
├── tasks/            # Scripts de tarefas
├── logs/             # Arquivos de log
├── configs/          # Arquivos de configuração
├── outputs/          # Resultados e relatórios
└── tests/            # Testes unitários
```

## GPU (Aceleração NVIDIA)

O projeto suporta aceleração GPU usando NVIDIA RTX 3080 ou superior para treinamento de modelos e cálculo de scores.

### Requisitos GPU

**Hardware:**
- NVIDIA GPU com arquitetura Pascal ou superior (GTX 1060+, RTX 2060+, RTX 3080 recomendada)
- Mínimo 4GB VRAM (8GB+ recomendado)
- CUDA Compute Capability 6.0+

**Software:**
- NVIDIA Driver 470.57.02+ (Windows) / 470.57.02+ (Linux)
- CUDA Toolkit 11.2+ (11.8 recomendado)
- cuML (RAPIDS) para machine learning em GPU

### Instalação CUDA e cuML

```bash
# 1. Instalar CUDA Toolkit (https://developer.nvidia.com/cuda-downloads)
# Baixar e instalar CUDA 11.8 para Windows

# 2. Instalar cuML via conda (recomendado)
conda create -n milionaria-gpu python=3.9
conda activate milionaria-gpu
conda install -c rapidsai -c conda-forge cuml=23.10 python=3.9 cudatoolkit=11.8

# 3. Instalar dependências do projeto
pip install -r requirements.txt

# 4. Verificar instalação
python -c "import cuml; print('cuML instalado com sucesso!')"
```

### Ativação do Modo GPU

**Método 1: Substituição direta no código**
```python
# Substituir imports CPU por GPU
# De:
from src.models.scoring import learn_weights_ridge, score_numbers

# Para:
from src.models.scoring_gpu import learn_weights_gpu, score_numbers_gpu

# Substituir chamadas de função
# De:
model, scaler, weights = learn_weights_ridge(features)
scores = score_numbers(snapshot, weights)

# Para:
model, scaler, weights = learn_weights_gpu(features, use_gpu=True)
scores = score_numbers_gpu(snapshot, weights, use_gpu=True)
```

**Método 2: Verificação automática**
```python
from src.models.scoring_gpu import get_gpu_info

# Verificar status da GPU
gpu_info = get_gpu_info()
print(f"GPU disponível: {gpu_info['cuml_available']}")
print(f"GPUs encontradas: {gpu_info['gpu_count']}")

if gpu_info['cuml_available']:
    # Usar GPU
    from src.models.scoring_gpu import learn_weights_gpu, score_numbers_gpu
    model, scaler, weights = learn_weights_gpu(features, use_gpu=True)
else:
    # Fallback para CPU
    from src.models.scoring import learn_weights_ridge, score_numbers
    model, scaler, weights = learn_weights_ridge(features)
```

### Performance GPU vs CPU

| Operação | CPU (i7-10700K) | GPU (RTX 3080) | Speedup |
|----------|-----------------|----------------|----------|
| Treinamento modelo | ~2.5s | ~0.3s | 8.3x |
| Cálculo scores | ~0.8s | ~0.1s | 8.0x |
| Validação walk-forward | ~45s | ~6s | 7.5x |

### Fallback Automático

O sistema possui fallback automático para CPU quando:
- cuML não está instalado
- GPU não está disponível
- `use_gpu=False` é especificado
- Erro durante operações GPU

### Troubleshooting GPU

**Erro: "cuML não disponível"**
```bash
# Verificar instalação CUDA
nvcc --version
nvidia-smi

# Reinstalar cuML
conda install -c rapidsai cuml --force-reinstall
```

**Erro: "CUDA out of memory"**
```python
# Reduzir batch size ou usar CPU para datasets grandes
model, scaler, weights = learn_weights_gpu(features, use_gpu=False)
```

**Verificar compatibilidade:**
```python
from src.models.scoring_gpu import get_gpu_info
info = get_gpu_info()
print(info)  # Mostra detalhes da GPU e memória
```

## Extração de Dados (ETL)

O módulo ETL fornece uma interface limpa para extrair dados dos sorteios do banco de dados em formato adequado para análise e modelagem de IA.

### Uso do Módulo ETL

```python
from src.etl.from_db import load_draws

# Carrega todos os sorteios do banco
df = load_draws("db/milionaria.db")

# Exibe informações básicas
print(f"Total de sorteios: {len(df)}")
print(f"Colunas: {df.columns}")
print(df.head())
```

### Estrutura dos Dados

O DataFrame retornado contém as seguintes colunas:
- `concurso` (int): Número do concurso
- `data` (date): Data do sorteio
- `D1, D2, D3, D4, D5, D6` (int): Dezenas sorteadas (1-50)
- `T1, T2` (int): Trevos sorteados (1-6)

### Tipos de Dados
- Números inteiros otimizados (Int8 para dezenas/trevos, Int32 para concurso)
- Datas como objetos `date` do Python
- DataFrame Polars para performance otimizada

## Scoring de Números

O módulo de scoring utiliza machine learning para calcular probabilidades de cada número aparecer no próximo sorteio.

### Uso do Módulo Scoring

```python
from src.etl.from_db import load_draws
from src.features.make import build_number_features, latest_feature_snapshot
from src.models.scoring import learn_weights_ridge, score_numbers, print_top_scores

# Carregar dados e gerar features
df = load_draws("db/milionaria.db")
features = build_number_features(df)
snapshot = latest_feature_snapshot(df)

# Treinar modelo Ridge e aprender pesos
model, scaler, weights = learn_weights_ridge(features)

# Calcular scores para dezenas (1-50)
scores = score_numbers(snapshot, weights)

# Mostrar top-10 números com maior probabilidade
print_top_scores(scores, top_k=10)
```

### Características do Scoring

- **Algoritmo**: Ridge Regression com regularização
- **Features**: Frequência, rolling windows, última aparição, momentum
- **Normalização**: Scores normalizados entre [0,1]
- **Determinístico**: Resultados reproduzíveis
- **Output**: Dicionário {numero: score} para dezenas 1-50

### Upgrade GPU (Futuro)

🚀 **Flag GPU**: Estrutura preparada para aceleração GPU com cuML (RAPIDS)

Quando necessário, o módulo `src.models.scoring_gpu.py` pode ser implementado para:
- Treinamento em GPU com cuML Ridge
- Processamento paralelo com cuDF/cuPy
- Speedup significativo para datasets grandes

**Pré-requisitos GPU**:
- NVIDIA GPU com CUDA
- cuML (RAPIDS)
- cuDF para DataFrames em GPU

## Instalação

### Pré-requisitos
- Python 3.11
- mamba ou conda
- polars (para ETL)
- scikit-learn (para scoring)

### Configuração do ambiente

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd milionaria-ai
```

2. Crie e ative o ambiente conda:
```bash
```bash
mamba env create -f environment.yml
mamba activate milionaria-ai
```

3. Instale as dependências adicionais:
```bash
pip install playwright tenacity
playwright install
```
mamba env create -f env.yml && mamba activate milionaria-ai
```

3. Instale o navegador Chromium para Playwright:
```bash
playwright install chromium
```

4. Verifique a instalação do Playwright:
```bash
playwright --version
```

## Como rodar rápido

### Teste do banco de dados

1. Criar e testar o banco de dados:
```bash
python tests/test_db.py
```

2. Verificar se o banco foi criado:
```bash
# Listar arquivos do banco
ls db/

# Conectar ao SQLite e listar tabelas
sqlite3 db/milionaria.db ".tables"

# Ver estrutura da tabela sorteios
sqlite3 db/milionaria.db ".schema sorteios"

# Contar registros
sqlite3 db/milionaria.db "SELECT COUNT(*) FROM sorteios;"
```

### Importação inicial

3. Preparar planilha histórica:
   - Coloque o arquivo `base_275.xlsx` na pasta `data/raw/`
   - A planilha deve conter as colunas: `concurso`, `data`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `T1`, `T2`
   - Datas no formato DD/MM/AAAA
   - Exemplo disponível em: `data/raw/exemplo_base_275.csv`

4. Importar planilha histórica:
```bash
python -m src.ingest.import_initial
```

5. Testar importação com dados de exemplo:
```bash
python tests/test_import.py
```

6. Verificar importação:
```bash
# Contar registros importados
sqlite3 db/milionaria.db "SELECT COUNT(*) as total_registros FROM sorteios;"

# Ver primeiros registros
sqlite3 db/milionaria.db "SELECT * FROM sorteios ORDER BY concurso LIMIT 5;"

# Ver últimos registros
sqlite3 db/milionaria.db "SELECT * FROM sorteios ORDER BY concurso DESC LIMIT 5;"
```

### Coleta da CAIXA

7. Coletar dados atuais do portal da CAIXA:
```python
# Exemplo de chamada assíncrona
import asyncio
from src.update.fetch_caixa import fetch_caixa_data

async def main():
    # Coleta apenas o concurso atual
    df_atual = await fetch_caixa_data(to_latest=False)
    print(f"Concurso atual: {df_atual.iloc[0]['concurso']}")
    
    # Coleta do concurso 100 até o último disponível
    df_range = await fetch_caixa_data(start_concurso=100, to_latest=True)
    print(f"Coletados {len(df_range)} concursos")
    
    # Snapshots HTML salvos em logs/html/ para auditoria
    print("Snapshots salvos para auditoria em logs/html/")

# Executar
asyncio.run(main())
```

### Validação de Integridade

8. Verificar integridade do banco de dados:
```bash
# Comando rápido para validação completa
python -m src.utils.validate
```

Este comando verifica:
- ✅ **Datas não nulas**: Todas as datas são válidas
- ✅ **Dezenas válidas**: d1-d6 estão no intervalo [1,50] <mcreference link="https://amazonasatual.com.br/comecam-as-apostas-da-milionaria-nova-loteria-da-caixa-com-premio-minimo-de-r-10-milhoes/" index="1">1</mcreference>
- ✅ **Trevos válidos**: t1,t2 estão no intervalo [1,6] <mcreference link="https://amazonasatual.com.br/comecam-as-apostas-da-milionaria-nova-loteria-da-caixa-com-premio-minimo-de-r-10-milhoes/" index="1">1</mcreference>
- ✅ **Concursos únicos**: Não há duplicatas

**Retorna `True` se todos os checks passarem**, caso contrário levanta exceção com detalhes do erro.

**Nota**: Os checks de integridade são executados automaticamente após cada atualização do banco via `update_db`.

### Automação e Agendamento

8. Script de atualização automática:
```powershell
# Executa atualização completa com logging
.\tasks\update_all.ps1
```

O script `tasks/update_all.ps1` automatiza todo o processo pós-sorteio:
- ✅ **Ativa ambiente conda** automaticamente
- ✅ **Executa atualização** do banco de dados
- ✅ **Valida integridade** dos dados
- ✅ **Gera logs detalhados** em `logs/update_YYYYMMDD.log`
- ✅ **Falha com exit code ≠ 0** em caso de erro
- ✅ **Reexecutável** e usa caminhos relativos

9. Configurar agendamento diário (Windows):
```powershell
# Abrir Agendador de Tarefas
taskschd.msc

# Ou via linha de comando:
schtasks /create /tn "Milionaria-AI Update" /tr "powershell.exe -ExecutionPolicy Bypass -File 'C:\caminho\completo\para\milionaria-ai\tasks\update_all.ps1'" /sc daily /st 21:30 /ru "SYSTEM"
```

**Configuração manual no Agendador de Tarefas:**
1. Abra o **Agendador de Tarefas** (`taskschd.msc`)
2. Clique em **"Criar Tarefa Básica"**
3. **Nome**: `Milionaria-AI Update`
4. **Disparador**: `Diariamente às 21:30`
5. **Ação**: `Iniciar um programa`
6. **Programa**: `powershell.exe`
7. **Argumentos**: `-ExecutionPolicy Bypass -File "C:\caminho\completo\para\milionaria-ai\tasks\update_all.ps1"`
8. **Iniciar em**: `C:\caminho\completo\para\milionaria-ai`
9. **Executar com privilégios mais altos**: ✅ Marcado

**Verificação do agendamento:**
```powershell
# Listar tarefas agendadas
schtasks /query /tn "Milionaria-AI Update"

# Executar manualmente para teste
schtasks /run /tn "Milionaria-AI Update"

# Verificar log após execução
Get-Content logs\update_$(Get-Date -Format 'yyyyMMdd').log -Tail 20
```

10. Testar coleta da CAIXA:
```bash
# Executa o teste integrado
python -m src.update.fetch_caixa
```

### Execução principal

9. Execute a coleta inicial:
```bash
python -m src.cli.main --collect
```

10. Processe os dados:
```bash
python -m src.cli.main --process
```

## Dependências do Playwright

### Configuração para Máquinas Novas

O projeto utiliza Playwright para web scraping. Em máquinas novas, é necessário instalar os navegadores:

```bash
# Instalar dependências Python
pip install playwright

# Instalar navegadores do Playwright (OBRIGATÓRIO)
playwright install

# Ou instalar apenas o Chromium (mais leve)
playwright install chromium
```

### Dependências do Sistema

**Windows:**
```bash
# Instalar Microsoft Visual C++ Redistributable se necessário
# Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

**macOS:**
```bash
# Dependências geralmente já estão disponíveis
# Se houver problemas, instalar Xcode Command Line Tools:
xcode-select --install
```

### Verificação da Instalação

```bash
# Testar se Playwright está funcionando
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Testar navegador
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop(); print('Browser OK')"
```

### Troubleshooting

- **Erro "Browser not found"**: Execute `playwright install`
- **Erro de permissões**: Execute como administrador/sudo
- **Erro de dependências**: Instale as dependências do sistema listadas acima
- **Timeout em sites**: Verifique conexão de internet e firewall

## Testes

O projeto inclui uma suíte de testes para garantir a estabilidade e qualidade do código.

### Executando os Testes

```bash
# Executar todos os testes com output mínimo
pytest -q

# Executar testes específicos
pytest tests/test_schema.py -v
pytest tests/test_parse.py -v
pytest tests/test_update.py -v

# Executar com cobertura
pytest --cov=src tests/
```

### Estrutura dos Testes

- **`test_schema.py`**: Testes para criação e estrutura do banco de dados
- **`test_parse.py`**: Testes para parser de HTML com fixtures de dados
- **`test_update.py`**: Testes para operações de atualização com mocks

### Pré-requisitos para Testes

```bash
# Instalar pytest se não estiver instalado
pip install pytest pytest-cov
```

## Funcionalidades

- ✅ Coleta automática de dados da +Milionária
- ✅ Armazenamento em banco SQLite
- ✅ Processamento e limpeza de dados
- ✅ Análise estatística
- ✅ Modelos de machine learning
- ✅ Simulação de resultados
- ✅ Geração de números baseada em IA
- ✅ Suíte de testes automatizados

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.