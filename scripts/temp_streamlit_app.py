
import streamlit as st
import sys
import os
from pathlib import Path

st.set_page_config(
    page_title="Milionária AI - Debug",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎯 Milionária AI - Versão Debug")
st.write("Esta é uma versão simplificada para debug.")

st.subheader("Informações do Sistema")
st.write(f"**Python Version:** {sys.version}")
st.write(f"**Working Directory:** {os.getcwd()}")

db_path = Path("db/milionaria.db")
config_path = Path("configs/config.yaml")

st.write(f"**Database Exists:** {db_path.exists()}")
st.write(f"**Config Exists:** {config_path.exists()}")

if st.button("Teste de Funcionalidade"):
    st.success("Botão funcionando corretamente!")
    st.balloons()

st.info("Se você está vendo esta mensagem, o Streamlit está funcionando!")
