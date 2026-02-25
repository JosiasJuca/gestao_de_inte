import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from src.database.operations import obter_historico
from src.utils.constants import CATEGORIAS, RESPONSAVEIS, RESPONSABILIDADE
from src.utils.helpers import formatar_data_br


def renderizar_historico():
    st.markdown("### Histórico de chamados resolvidos")


    col1, col2, col3 = st.columns(3)
    with col1:
        data_inicio = st.date_input(
            "De", value=date.today() - timedelta(days=30), key="hist_inicio"
        )
    with col2:
        data_fim = st.date_input("Até", value=date.today(), key="hist_fim")
    with col3:
        filtro_resp = st.selectbox("Responsável", ["Todos"] + RESPONSAVEIS, key="hist_resp")

    chamados = obter_historico()

    if not chamados:
        st.info("Nenhum chamado resolvido encontrado.")
        return

    linhas = []
    for c in chamados:
        linhas.append({
            "Cliente": c["cliente_nome"],
            "Título": c["titulo"],
            "Responsável": c["responsavel"],
            "Abertura": formatar_data_br(c["data_abertura"]),
            "Resolução": formatar_data_br(c["data_resolucao"]),
        })

    df_tabela = pd.DataFrame(linhas)
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    # Export CSV
    csv = df_tabela.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "⬇️ Exportar CSV",
        data=csv,
        file_name="historico_completo.csv",
        mime="text/csv",
    )
