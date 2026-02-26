from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from src.database.operations import init_db, obter_estatisticas
from src.utils.constants import CSS_STYLES
from src.utils.helpers import exibir_mensagens_persistentes
from src.components.dashboard import renderizar_dashboard
from src.components.chamados import renderizar_chamados, renderizar_form_rapido
from src.components.checklist import renderizar_checklist
from src.components.historico import renderizar_historico
from src.components.clientes import renderizar_gestao_clientes
from src.components.cobrancas_lista import renderizar_cobrancas_lista
from src.components.regras import renderizar_regras

st.set_page_config(
    page_title="Gestão de Integrações",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Adiciona espaçamento entre as abas
TABS_SPACING_CSS = """
<style>
.stTabs [data-baseweb="tab-list"] {
    gap: 24px !important;
}
</style>
"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)
st.markdown(TABS_SPACING_CSS, unsafe_allow_html=True)

init_db()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Gestão de Integrações")
    st.markdown("---")

    # Métricas rápidas
    try:
        stats = obter_estatisticas()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Abertos", stats["total_abertos"])
        with col2:
            st.metric("Ag. cliente", stats["aguardando_cliente"])
    except Exception:
        pass

    st.markdown("---")

    # Adição rápida
    st.markdown("**Abertura rápida**")
    renderizar_form_rapido()

    st.markdown("---")

    # Gestão de clientes
    with st.expander("Clientes", expanded=False):
        renderizar_gestao_clientes()

# ─── ABAS PRINCIPAIS ──────────────────────────────────────────────────────────
exibir_mensagens_persistentes()

aba_dash, aba_chamados, aba_cobrancas, aba_checklist, aba_hist, aba_regras = st.tabs([
    "Dashboard",
    "Chamados",
    "Cobranças",
    "Checklist",
    "Histórico",
    "Regras",
])

with aba_dash:
    renderizar_dashboard()

with aba_chamados:
    renderizar_chamados()

with aba_cobrancas:
    renderizar_cobrancas_lista()

with aba_checklist:
    renderizar_checklist()

with aba_hist:
    renderizar_historico()

with aba_regras:
    renderizar_regras()
