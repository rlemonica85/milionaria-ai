# Milionária AI - Executável Streamlit

## 📋 Sobre

Este executável (`MilionariaStreamlit.exe`) contém a interface web completa do Milionária AI empacotada em um único arquivo executável. Não é necessário instalar Python ou dependências - tudo está incluído!

## 🚀 Como Usar

### Opção 1: Script Automático (Recomendado)

**Windows Batch:**
```bash
MilionariaStreamlit.bat
```

**PowerShell:**
```powershell
.\MilionariaStreamlit.ps1
```

### Opção 2: Execução Direta

```bash
dist\MilionariaStreamlit.exe
```

Depois acesse: http://localhost:8501

## 📁 Arquivos Incluídos

- `MilionariaStreamlit.exe` - Executável principal
- `MilionariaStreamlit.bat` - Script de inicialização (Windows)
- `MilionariaStreamlit.ps1` - Script de inicialização (PowerShell)
- `README_EXECUTAVEL_STREAMLIT.md` - Este arquivo

## 🎯 Funcionalidades

### Interface Web Completa
- ✅ Configuração de parâmetros via interface gráfica
- ✅ Execução do pipeline completo
- ✅ Visualização de resultados e métricas
- ✅ Exportação de bilhetes em Excel
- ✅ Backtest paralelo com Ray
- ✅ Gráficos e estatísticas interativas

### Pipeline Incluído
1. **Carregamento de dados** - Banco SQLite integrado
2. **Geração de features** - Análise estatística avançada
3. **Treinamento de modelo** - Ridge Regression otimizado
4. **Geração de candidatos** - Algoritmos de seleção inteligente
5. **Aplicação de filtros** - Configurações personalizáveis
6. **Atribuição de trevos** - Estratégias múltiplas
7. **Backtest paralelo** - Validação histórica
8. **Ranking por score** - Ordenação por performance

## ⚙️ Configurações

### Parâmetros Principais
- **Banco de dados:** `db/milionaria.db` (incluído)
- **Configurações:** `configs/filters.yaml` (incluído)
- **Seed:** Para reprodutibilidade dos resultados
- **Top K:** Quantidade de bilhetes a exibir

### Filtros Disponíveis
- Soma das dezenas
- Números pares/ímpares
- Sequências consecutivas
- Distribuição por colunas
- Padrões estatísticos

## 📊 Como Usar a Interface

1. **Inicie o executável** usando um dos métodos acima
2. **Configure os parâmetros** na barra lateral esquerda:
   - Caminho do banco de dados
   - Arquivo de configuração
   - Seed para reprodutibilidade
   - Número de bilhetes (Top K)
3. **Clique em "Gerar Jogos"** para executar o pipeline
4. **Visualize os resultados:**
   - Ranking dos melhores bilhetes
   - Métricas de performance
   - Estatísticas detalhadas
5. **Exporte para Excel** se desejar salvar os bilhetes

## 🔧 Solução de Problemas

### Executável não inicia
- Verifique se o arquivo `dist/MilionariaStreamlit.exe` existe
- Execute como administrador se necessário
- Verifique se o antivírus não está bloqueando

### Interface não abre no navegador
- Acesse manualmente: http://localhost:8501
- Verifique se a porta 8501 não está em uso
- Aguarde alguns segundos para o servidor inicializar

### Erro durante execução
- Verifique se os arquivos `db/milionaria.db` e `configs/filters.yaml` existem
- Reinicie o executável
- Verifique os logs no terminal

### Performance lenta
- O primeiro carregamento pode demorar mais
- Reduza o valor de Top K para testes
- Feche outros programas pesados

## 📝 Logs e Debugging

- **Logs do Streamlit:** `logs/streamlit_debug.log`
- **Logs do CLI:** `logs/milionaria_cli.log`
- **Métricas:** `logs/metrics.csv`
- **Terminal:** Mostra logs em tempo real

## 🎮 Exemplos de Uso

### Geração Rápida (5 bilhetes)
1. Seed: `42`
2. Top K: `5`
3. Clique em "Gerar Jogos"
4. Aguarde ~30 segundos
5. Visualize os 5 melhores bilhetes

### Análise Completa (50 bilhetes)
1. Seed: `123`
2. Top K: `50`
3. Clique em "Gerar Jogos"
4. Aguarde ~2-3 minutos
5. Analise métricas detalhadas
6. Exporte para Excel

## 🔄 Atualizações

Para atualizar o sistema:
1. Use o executável `MilionariaUpdate.exe` para atualizar dados
2. Recompile o executável Streamlit se necessário:
   ```bash
   pyinstaller app_streamlit.spec
   ```

## 📞 Suporte

Em caso de problemas:
1. Verifique este README
2. Consulte os logs de erro
3. Teste com o Python direto: `streamlit run app_streamlit.py`
4. Recompile o executável se necessário

---

**Milionária AI** - Sistema inteligente para análise e geração de jogos da +Milionária

*Executável gerado com PyInstaller - Versão standalone completa*