"""Interface Streamlit para exploração de scores e jogos da +Milionária.

Este aplicativo fornece uma interface web interativa para:
- Configurar parâmetros de geração
- Executar o pipeline completo
- Visualizar resultados e métricas
- Exportar bilhetes em Excel
"""

import streamlit as st
import pandas as pd
import time
from pathlib import Path
import os
import yaml
from datetime import datetime
import traceback
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/streamlit_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar módulos do projeto
try:
    from src.etl.from_db import load_draws
    from src.features.make import build_number_features, latest_feature_snapshot
    from src.models.scoring import learn_weights_ridge, score_numbers
    from src.generate.tickets import load_filters_config, generate_candidates, apply_filters, assign_trevos
    from src.simulate.backtest_ray import run_backtest_parallel, print_backtest_summary
    from src.generate.export import export_excel, format_ticket_display
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="+Milionária AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🎯 +Milionária AI - Interface de Exploração")
st.markdown("---")

# Sidebar para configurações
st.sidebar.header("⚙️ Configurações")

# Inputs de configuração
db_path = st.sidebar.text_input(
    "📊 Banco de Dados",
    value="db/milionaria.db",
    help="Caminho para o arquivo do banco de dados"
)

config_path = st.sidebar.text_input(
    "📋 Arquivo de Configuração",
    value="configs/filters.yaml",
    help="Caminho para o arquivo de configuração YAML"
)

seed = st.sidebar.number_input(
    "🎲 Seed (Reprodutibilidade)",
    min_value=1,
    max_value=9999,
    value=42,
    help="Seed para garantir resultados reproduzíveis"
)

top_k = st.sidebar.number_input(
    "🏆 Top K Bilhetes",
    min_value=1,
    max_value=100,
    value=10,
    help="Número de melhores bilhetes para exibir"
)

export_filename = st.sidebar.text_input(
    "📄 Nome do Arquivo de Exportação",
    value="jogos_streamlit.xlsx",
    help="Nome do arquivo Excel para exportação"
)

# Botão principal de geração
st.sidebar.markdown("---")
generate_button = st.sidebar.button(
    "🚀 Gerar Jogos",
    type="primary",
    use_container_width=True
)

# Área principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📈 Resultados")
    
with col2:
    st.header("📊 Métricas")

# Estado da sessão para armazenar resultados
if 'results' not in st.session_state:
    st.session_state.results = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None

# Função principal de execução
def run_pipeline(db_path, config_path, seed, top_k):
    """Executa o pipeline completo e retorna resultados."""
    try:
        logger.info("Iniciando pipeline completo")
        
        # 1. Carregar dados
        with st.spinner("📥 Carregando dados do banco..."):
            df = load_draws(db_path)
            logger.info(f"Dados carregados: {len(df)} registros")
            st.success(f"✅ {len(df)} sorteios carregados")
        
        # 2. Gerar features e treinar modelo
        with st.spinner("🧠 Gerando features e treinando modelo..."):
            logger.info("Gerando features...")
            features = build_number_features(df)
            logger.info(f"Features geradas: {features.shape}")
            
            snapshot = latest_feature_snapshot(df)
            logger.info(f"Snapshot gerado: {snapshot.shape}")
            
            model, scaler, weights = learn_weights_ridge(features)
            logger.info(f"Modelo treinado com {len(features)} amostras")
            
            scores = score_numbers(snapshot, weights)
            logger.info(f"Scores calculados para {len(scores)} números")
            
            # Selecionar apenas colunas numéricas para o scaler
            numeric_features = features.select([
                'freq_total', 'roll10', 'roll25', 'last_seen', 'momentum5'
            ])
            
            r2_score = model.score(
                scaler.transform(numeric_features.to_numpy()),
                features.select('y_next').to_numpy().ravel()
            )
            
            st.success(f"✅ Modelo treinado (R² = {r2_score:.4f})")
            st.success(f"✅ Scores calculados para {len(scores)} números")
        
        # 3. Gerar candidatos e aplicar filtros
        with st.spinner("🎲 Gerando candidatos e aplicando filtros..."):
            logger.info("Carregando configuração de filtros...")
            config = load_filters_config(config_path)
            
            candidates = generate_candidates(
                scores, 
                k=config['generation']['k'],
                top_pool=config['generation']['top_pool'],
                n=config['generation']['n'],
                seed=seed
            )
            logger.info(f"Candidatos gerados: {len(candidates)}")
            
            filtered_tickets = apply_filters(candidates, config['filters'])
            approval_rate = len(filtered_tickets) / len(candidates) * 100
            logger.info(f"Tickets filtrados: {len(filtered_tickets)} ({approval_rate:.1f}% aprovação)")
            
            complete_tickets = assign_trevos(
                filtered_tickets, 
                strategy=config['trevos']['strategy'],
                seed=seed
            )
            
            # Pegar apenas os top_k melhores
            complete_tickets = complete_tickets[:config['output']['top_k']]
            logger.info(f"Bilhetes completos: {len(complete_tickets)}")
            
            st.success(f"✅ {len(candidates)} candidatos gerados")
            st.success(f"✅ {len(filtered_tickets)} tickets após filtros ({approval_rate:.1f}% aprovação)")
            st.success(f"✅ {len(complete_tickets)} bilhetes completos gerados")
        
        # 4. Executar backtest
        with st.spinner("📈 Executando backtest paralelo..."):
            logger.info("Iniciando backtest paralelo...")
            results = run_backtest_parallel(complete_tickets, df)
            logger.info(f"Backtest concluído: {len(results)} resultados")
            st.success(f"✅ Backtest concluído para {len(results)} bilhetes")
        
        # Ordenar por score e pegar top_k
        results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)[:top_k]
        
        # Calcular métricas gerais
        metrics = {
            'total_bilhetes': len(results),
            'score_medio': sum(r['score'] for r in results) / len(results),
            'melhor_score': max(r['score'] for r in results),
            'acertos_medios_dezenas': sum(r['avg_hits_dezenas'] for r in results) / len(results),
            'bilhetes_4_plus': sum(1 for r in results if r['max_hits_dezenas'] >= 4),
            'bilhetes_1_trevo_plus': sum(1 for r in results if r['max_hits_trevos'] >= 1),
            'r2_score': r2_score,
            'approval_rate': approval_rate,
            'weights': weights
        }
        
        logger.info("Pipeline concluído com sucesso")
        return results_sorted, metrics, results
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro durante pipeline: {error_msg}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        
        if "could not convert string to float" in error_msg and "dezena" in error_msg:
            st.error("❌ Erro de conversão detectado: Problema com dados contendo 'dezena'")
            st.error("💡 Sugestão: Verifique se há dados corrompidos ou configurações incorretas")
            st.info("🔧 Tentando executar com validação adicional...")
            logger.warning("Tentando recuperação com validação de dados")
            
            # Tentar novamente com validação extra
            try:
                # Recarregar dados com validação
                df_clean = load_draws(db_path)
                logger.info(f"Dados recarregados: {len(df_clean)} registros")
                
                # Verificar se há problemas nos dados
                if 'tipo' in df_clean.columns:
                    unique_tipos = df_clean['tipo'].unique().to_list()
                    st.info(f"Tipos únicos encontrados: {unique_tipos}")
                    logger.info(f"Tipos únicos: {unique_tipos}")
                    
                    # Filtrar apenas dados válidos
                    df_clean = df_clean.filter(pl.col('tipo').is_in(['dezena', 'trevo']))
                    st.info(f"Dados filtrados: {df_clean.shape[0]} registros")
                    logger.info(f"Dados filtrados: {df_clean.shape[0]} registros")
                
                # Tentar pipeline novamente com dados limpos
                features_clean = build_number_features(df_clean)
                snapshot_clean = latest_feature_snapshot(df_clean)
                
                st.success("✅ Dados validados e pipeline reiniciado")
                logger.info("Validação bem-sucedida")
                return None, None, None  # Retornar para permitir nova tentativa
                
            except Exception as retry_error:
                logger.error(f"Erro na recuperação: {str(retry_error)}")
                logger.error(f"Traceback da recuperação: {traceback.format_exc()}")
                st.error(f"❌ Erro persistente após validação: {str(retry_error)}")
                st.error("📋 Detalhes técnicos para debug:")
                st.code(f"Erro original: {error_msg}\nErro na validação: {str(retry_error)}")
        else:
            st.error(f"❌ Erro durante execução: {error_msg}")
            
        return None, None, None

# Executar pipeline quando botão for pressionado
if generate_button:
    # Validar inputs
    if not os.path.exists(db_path):
        st.error(f"❌ Banco de dados não encontrado: {db_path}")
    elif not os.path.exists(config_path):
        st.error(f"❌ Arquivo de configuração não encontrado: {config_path}")
    else:
        start_time = time.time()
        
        results, metrics, all_results = run_pipeline(db_path, config_path, seed, top_k)
        
        if results and metrics:
            st.session_state.results = results
            st.session_state.metrics = metrics
            st.session_state.all_results = all_results
            
            execution_time = time.time() - start_time
            st.success(f"⏱️ Pipeline concluído em {execution_time:.2f}s")

# Exibir resultados se disponíveis
if st.session_state.results and st.session_state.metrics:
    results = st.session_state.results
    metrics = st.session_state.metrics
    
    # Coluna de resultados
    with col1:
        st.subheader(f"🏆 Top {len(results)} Bilhetes")
        
        # Criar DataFrame para exibição
        display_data = []
        for i, result in enumerate(results, 1):
            display_data.append({
                'Rank': i,
                'Score': f"{result['score']:.4f}",
                'Avg Dez': f"{result['avg_hits_dezenas']:.2f}",
                'Avg Trev': f"{result['avg_hits_trevos']:.2f}",
                'Max Dez': result['max_hits_dezenas'],
                'Max Trev': result['max_hits_trevos'],
                'Bilhete': format_ticket_display((result['dezenas'], result['trevos']))
            })
        
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True)
        
        # Melhor bilhete em destaque
        if results:
            best = results[0]
            st.subheader("🥇 Melhor Bilhete")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Score", f"{best['score']:.4f}")
                st.metric("Acertos Médios (Dezenas)", f"{best['avg_hits_dezenas']:.2f}")
                st.metric("Acertos Médios (Trevos)", f"{best['avg_hits_trevos']:.2f}")
            
            with col_b:
                st.metric("Máximo Acertos (Dezenas)", best['max_hits_dezenas'])
                st.metric("Máximo Acertos (Trevos)", best['max_hits_trevos'])
                st.metric("Sorteios com Acertos", len(best['winning_draws']))
            
            # Exibir bilhete formatado
            dezenas_str = '-'.join([f"{int(d):02d}" for d in best['dezenas']])
            trevos_str = '-'.join([str(int(t)) for t in best['trevos']])
            st.code(f"Dezenas: {dezenas_str}\nTrevos: {trevos_str}", language=None)
    
    # Coluna de métricas
    with col2:
        st.subheader("📊 Estatísticas Gerais")
        
        st.metric("Total de Bilhetes", metrics['total_bilhetes'])
        st.metric("Score Médio", f"{metrics['score_medio']:.4f}")
        st.metric("Melhor Score", f"{metrics['melhor_score']:.4f}")
        st.metric("Acertos Médios (Dezenas)", f"{metrics['acertos_medios_dezenas']:.2f}")
        st.metric("Bilhetes com 4+ Acertos", metrics['bilhetes_4_plus'])
        st.metric("Bilhetes com 1+ Trevo", metrics['bilhetes_1_trevo_plus'])
        
        st.subheader("🤖 Modelo")
        st.metric("R² Score", f"{metrics['r2_score']:.4f}")
        st.metric("Taxa de Aprovação", f"{metrics['approval_rate']:.1f}%")
        
        # Pesos do modelo
        st.subheader("⚖️ Pesos do Modelo")
        for feature, weight in metrics['weights'].items():
            st.metric(feature, f"{float(weight):.4f}")
    
    # Seção de exportação
    st.markdown("---")
    st.header("📄 Exportação")
    
    col_export1, col_export2 = st.columns([3, 1])
    
    with col_export1:
        st.write(f"Exportar todos os {metrics['total_bilhetes']} bilhetes para Excel:")
    
    with col_export2:
        if st.button("📥 Exportar Excel", type="secondary"):
            try:
                # Preparar dados para exportação
                export_path = f"outputs/{export_filename}"
                tickets_for_export = []
                
                for result in st.session_state.all_results:
                    tickets_for_export.append((result['dezenas'], result['trevos']))
                
                export_excel(tickets_for_export, export_path)
                
                st.success(f"✅ {len(tickets_for_export)} bilhetes exportados para: {export_path}")
                
                # Oferecer download
                if os.path.exists(export_path):
                    with open(export_path, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Excel",
                            data=file.read(),
                            file_name=export_filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
            except Exception as e:
                st.error(f"❌ Erro na exportação: {str(e)}")

else:
    # Tela inicial
    with col1:
        st.info("👈 Configure os parâmetros na barra lateral e clique em 'Gerar Jogos' para começar.")
        
        st.subheader("📋 Como usar:")
        st.markdown("""
        1. **Configure** o banco de dados e arquivo de configuração
        2. **Ajuste** a seed para reprodutibilidade
        3. **Defina** quantos bilhetes exibir (Top K)
        4. **Clique** em 'Gerar Jogos' para executar o pipeline
        5. **Visualize** os resultados e métricas
        6. **Exporte** os bilhetes em Excel se desejar
        """)
    
    with col2:
        st.subheader("ℹ️ Informações")
        st.markdown("""
        **Pipeline inclui:**
        - Carregamento de dados históricos
        - Geração de features
        - Treinamento de modelo Ridge
        - Geração de candidatos
        - Aplicação de filtros
        - Atribuição de trevos
        - Backtest paralelo
        - Ranking por score
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>🎯 +Milionária AI - Interface Streamlit</div>",
    unsafe_allow_html=True
)