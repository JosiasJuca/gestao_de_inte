import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.database.operations import obter_estatisticas
from src.utils.helpers import formatar_data_br, calcular_dias_aberto, cor_dias_aberto
from src.utils.constants import CORES_STATUS, CORES_STATUS_IMPLANTACAO


def renderizar_dashboard():
    stats = obter_estatisticas()

    _renderizar_kpis(stats)
    st.markdown("---")

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        _renderizar_grafico_categorias(stats)
    with col_graf2:
        _renderizar_grafico_clientes(stats)

    st.markdown("---")
    _renderizar_chamados_antigos(stats)

    if stats["cobrancas_sem_resposta"] > 0:
        st.warning(
            f"⏰ **{stats['cobrancas_sem_resposta']} cobrança(s)** enviada(s) há mais de 3 dias sem resposta do cliente."
        )


def _renderizar_kpis(stats):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Abertos", stats["total_abertos"])
    with c2:
        delta = "urgente" if stats["aguardando_cliente"] > 0 else None
        st.metric("Aguardando cliente", stats["aguardando_cliente"], delta=delta)
    with c3:
        st.metric("Resolvidos (30 dias)", stats["resolvidos_30d"])
    with c4:
        st.metric("Taxa de resolução", f"{stats['taxa_resolucao']}%")


def _renderizar_grafico_categorias(stats):
    dados = stats["por_categoria"]
    if not dados:
        st.info("Sem dados por categoria.")
        return

    labels = [d["categoria"] for d in dados if d["total"] > 0]
    values = [d["total"] for d in dados if d["total"] > 0]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        textinfo="label+value",
        marker=dict(line=dict(width=0, color='rgba(0,0,0,0)')),
        hovertemplate="%{label}: %{value} chamado(s)<extra></extra>",
    )])
    fig.update_layout(
        title="Chamados abertos por categoria",
        showlegend=False,
        height=320,
        margin=dict(t=40, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)


def _renderizar_grafico_clientes(stats):
    dados = stats["por_cliente"]
    if not dados:
        st.info("Sem dados por cliente.")
        return
    nomes = [d["cliente"] for d in dados]
    abertos = [d.get("abertos", 0) for d in dados]
    resolvidos = [d.get("resolvidos", 0) for d in dados]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=nomes,
            y=abertos,
            name="Abertos",
            marker_color="#0d6efd",
            text=[v if v > 0 else "" for v in abertos],
            textposition="outside",
            hovertemplate="%{x}: %{y} aberto(s)<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=nomes,
            y=resolvidos,
            name="Resolvidos",
            marker_color="#198754",
            text=[v if v > 0 else "" for v in resolvidos],
            textposition="outside",
            hovertemplate="%{x}: %{y} resolvido(s)<extra></extra>",
        )
    )

    fig.update_layout(
        title="Chamados por cliente",
        barmode="group",
        height=300,
        margin=dict(t=40, b=10, l=10, r=10),
        xaxis_tickangle=-45,
        yaxis=dict(visible=False),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    st.plotly_chart(fig, use_container_width=True)


_CSS_TABELA = """
<style>
.ch-table { width:100%; border-collapse:collapse; font-size:13px; }
.ch-table thead tr { background:#f0f2f6; }
.ch-table th {
    padding: 9px 12px;
    text-align: left;
    font-weight: 700;
    border-bottom: 2px solid #dee2e6;
    white-space: nowrap;
}
.ch-table th.center, .ch-table td.center { text-align: center; }
.ch-table td {
    padding: 9px 12px;
    border-bottom: 1px solid #f0f2f6;
    vertical-align: middle;
}
.ch-table tr:hover td { background: #f8f9fa; }
.ch-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    color: white;
    white-space: nowrap;
}
.ch-resp-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
}
.dias-cell { font-weight: 700; font-size: 14px; text-align: center; }
.dias-verde   { color: #198754; }
.dias-amarelo { color: #e6a817; }
.dias-laranja { color: #fd7e14; }
.dias-vermelho{ color: #dc3545; }
</style>
"""

_COR_DIAS = {
    "dias-verde":    "#198754",
    "dias-amarelo":  "#e6a817",
    "dias-laranja":  "#fd7e14",
    "dias-vermelho": "#dc3545",
}
_COR_RESP = {"Interna": "#0d6efd", "Cliente": "#fd7e14"}


def _renderizar_chamados_antigos(stats):
    antigos = stats["mais_antigos"]
    if not antigos:
        st.success("Nenhum chamado em aberto.")
        return

    st.markdown(_CSS_TABELA, unsafe_allow_html=True)

    col_titulo, col_total = st.columns([6, 1])
    with col_titulo:
        st.markdown("#### Chamados em aberto")
    with col_total:
        st.markdown(
            f'<div style="text-align:right;padding-top:18px;color:#6c757d;font-size:13px">'
            f'{len(antigos)} chamado(s)</div>',
            unsafe_allow_html=True,
        )

    linhas = []
    for ch in antigos:
        dias = calcular_dias_aberto(ch["data_abertura"])
        css  = cor_dias_aberto(dias)
        cor_dias = _COR_DIAS.get(css, "#6c757d")
        cor_status = CORES_STATUS.get(ch["status"], "#6c757d")
        si = ch.get("cliente_status_implantacao") or "3. Novo cliente sem integração"
        cor_si = CORES_STATUS_IMPLANTACAO.get(si, "#6c757d")

        linhas.append(
            f'<tr>'
            f'<td><strong>{ch["cliente_nome"]}</strong></td>'
            f'<td>{ch["titulo"]}</td>'
            f'<td class="center">{ch["categoria"]}</td>'
            f'<td class="center">'
            f'  <span class="ch-badge" style="background:{cor_si};font-size:11px">{si}</span>'
            f'</td>'
            f'<td class="center">'
            f'  <span class="ch-badge" style="background:{cor_status}">{ch["status"]}</span>'
            f'</td>'
            f'<td class="center">{ch["responsavel"]}</td>'
            f'<td class="center" style="white-space:nowrap">{formatar_data_br(ch["data_abertura"])}</td>'
            f'<td class="center">'
            f'  <span class="dias-cell" style="color:{cor_dias}">{dias}d</span>'
            f'</td>'
            f'</tr>'
        )

    html = (
        '<table class="ch-table"><thead><tr>'
        '<th>Cliente</th>'
        '<th>Título</th>'
        '<th class="center">Categoria</th>'
        '<th class="center">Implantação</th>'
        '<th class="center">Status</th>'
        '<th class="center">Responsável</th>'
        '<th class="center">Abertura</th>'
        '<th class="center">Dias aberto</th>'
        '</tr></thead><tbody>'
        + "".join(linhas)
        + "</tbody></table>"
    )
    st.markdown(html, unsafe_allow_html=True)
