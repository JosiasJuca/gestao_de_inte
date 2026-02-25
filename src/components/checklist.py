import streamlit as st
from src.database.operations import (
    obter_checklist_completo,
    atualizar_status_modulo,
    listar_clientes,
    listar_chamados_abertos,
)
from src.utils.constants import (
    MODULOS_CHECKLIST,
    RESPONSAVEIS,
    ICONES_CHECKLIST,
    CORES_CHECKLIST,
    STATUS_CHECKLIST,
    STATUS_IMPLANTACAO,
    CORES_STATUS_IMPLANTACAO,
)
from src.utils.helpers import adicionar_mensagem


_LABEL_STATUS = {
    "ok": "✓ OK",
    "problema": "✗ Problema",
    "construcao": "🛠 Em construção",
    "na": "— N/A",
}

_CSS_CHECKLIST = """
<style>
.ck-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.ck-table th {
    background: #f0f2f6;
    padding: 10px 6px;
    text-align: center;
    font-weight: 700;
    border: 1px solid #dee2e6;
    white-space: nowrap;
}
.ck-table th.col-cliente { text-align: left; padding-left: 12px; min-width: 160px; }
.ck-table td {
    border: 1px solid #dee2e6;
    text-align: center;
    padding: 8px 4px;
    font-size: 16px;
    font-weight: 700;
    cursor: default;
}
.ck-table td.col-cliente {
    text-align: left;
    padding-left: 12px;
    font-size: 13px;
    font-weight: 400;
}
.ck-table td.col-cliente strong { font-size: 14px; }
.ck-table tr:hover td { filter: brightness(0.95); }
.cell-ok       { background: #d1f5e0; color: #0a6640; }
.cell-problema { background: #fde8e8; color: #b91c1c; }
.cell-construcao { background: #dbeafe; color: #1d4ed8; }
.cell-na       { background: #f1f5f9; color: #94a3b8; }
.resumo-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    margin-left: 6px;
}
.impl-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    color: white;
    white-space: nowrap;
}
.ck-table th.col-impl { min-width: 130px; }
.ck-table td.col-impl { text-align: center; }
</style>
"""


def renderizar_checklist():
    st.markdown(_CSS_CHECKLIST, unsafe_allow_html=True)
    st.markdown("### Checklist de Integrações")

    clientes = listar_clientes()
    if not clientes:
        st.info("Nenhum cliente cadastrado. Adicione clientes na barra lateral.")
        return

    col_f1, col_f2, _ = st.columns([2, 2, 3])
    with col_f1:
        filtro_resp = st.selectbox(
            "Responsável",
            ["Todos"] + RESPONSAVEIS,
            key="checklist_filtro_resp",
        )
    with col_f2:
        filtro_status = st.selectbox(
            "Mostrar",
            ["Todos", "Com problemas", "Com pendências (não ok)"],
            key="checklist_filtro_status",
        )

    checklist_raw = obter_checklist_completo()
    chamados_abertos = listar_chamados_abertos()

    # Montar estrutura: {cliente_id: {modulo: row}}
    dados: dict = {}
    for row in checklist_raw:
        cid = row["cliente_id"]
        if cid not in dados:
            dados[cid] = {
                "id": cid,
                "nome": row["cliente_nome"],
                "responsavel": row["cliente_responsavel"],
                "status_implantacao": row["cliente_status_implantacao"] or "3. Novo cliente sem integração",
                "modulos": {},
            }
        dados[cid]["modulos"][row["modulo"]] = dict(row)

    # Filtrar por responsável
    if filtro_resp != "Todos":
        dados = {k: v for k, v in dados.items() if v["responsavel"] == filtro_resp}

    # Filtrar por status
    if filtro_status == "Com problemas":
        dados = {
            k: v for k, v in dados.items()
            if any(m.get("status") == "problema" for m in v["modulos"].values())
        }
    elif filtro_status == "Com pendências (não ok)":
        dados = {
            k: v for k, v in dados.items()
            if any(m.get("status") != "ok" for m in v["modulos"].values())
        }

    if not dados:
        st.info("Nenhum cliente encontrado com esse filtro.")
        return

    # ── Resumo rápido ──────────────────────────────────────────────────────────
    total_clientes = len(dados)
    total_problemas = sum(
        1 for v in dados.values()
        for m in v["modulos"].values() if m.get("status") == "problema"
    )
    total_construcao = sum(
        1 for v in dados.values()
        for m in v["modulos"].values() if m.get("status") == "construcao"
    )
    total_na = sum(
        1 for v in dados.values()
        for m in v["modulos"].values() if m.get("status") == "na"
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Clientes", total_clientes)
    with c2:
        st.metric("Problemas", total_problemas)
    with c3:
        st.metric("Em construção", total_construcao)
    with c4:
        st.metric("N/A", total_na)

    st.markdown("---")

    # ── Tabela HTML visual ─────────────────────────────────────────────────────
    html = ['<table class="ck-table">']
    html.append('<thead><tr>')
    html.append('<th class="col-cliente">Cliente</th>')
    html.append('<th class="col-impl">Implantação</th>')
    for mod in MODULOS_CHECKLIST:
        html.append(f'<th>{mod}</th>')
    html.append('<th>Resumo</th>')
    html.append('</tr></thead><tbody>')

    for cid, info in dados.items():
        n_prob = sum(1 for m in info["modulos"].values() if m.get("status") == "problema")
        n_const = sum(1 for m in info["modulos"].values() if m.get("status") == "construcao")

        if n_prob > 0:
            badge = f'<span class="resumo-badge" style="background:#fde8e8;color:#b91c1c">{n_prob} problema(s)</span>'
        elif n_const > 0:
            badge = f'<span class="resumo-badge" style="background:#dbeafe;color:#1d4ed8">{n_const} em construção</span>'
        else:
            badge = '<span class="resumo-badge" style="background:#d1f5e0;color:#0a6640">tudo ok</span>'

        si = info["status_implantacao"]
        cor_si = CORES_STATUS_IMPLANTACAO.get(si, "#6c757d")

        html.append('<tr>')
        html.append(
            f'<td class="col-cliente"><strong>{info["nome"]}</strong><br>'
            f'<small style="color:#6c757d">{info["responsavel"]}</small></td>'
        )
        html.append(
            f'<td class="col-impl">'
            f'<span class="impl-badge" style="background:{cor_si}">{si}</span>'
            f'</td>'
        )
        for mod in MODULOS_CHECKLIST:
            row = info["modulos"].get(mod)
            st_mod = row["status"] if row else "ok"
            icone = ICONES_CHECKLIST[st_mod]
            css_class = f"cell-{st_mod}"
            label = _LABEL_STATUS[st_mod]
            html.append(f'<td class="{css_class}" title="{mod}: {label}">{icone}</td>')

        html.append(f'<td style="text-align:center">{badge}</td>')
        html.append('</tr>')

    html.append('</tbody></table>')
    st.markdown("\n".join(html), unsafe_allow_html=True)

    # ── Legenda ────────────────────────────────────────────────────────────────
    st.markdown("")
    leg = " &nbsp;&nbsp; ".join(
        f'<span style="background:{CORES_CHECKLIST[k]}22;color:{CORES_CHECKLIST[k]};'
        f'padding:3px 10px;border-radius:8px;font-weight:600;font-size:13px">'
        f'{ICONES_CHECKLIST[k]} {label}</span>'
        for k, label in _LABEL_STATUS.items()
    )
    st.markdown(f"**Legenda:** {leg}", unsafe_allow_html=True)

    st.markdown("---")

    # ── Seção de edição ────────────────────────────────────────────────────────
    st.markdown("#### Editar status")
    st.caption("Selecione o cliente e o módulo que deseja atualizar.")

    nomes_clientes = {info["nome"]: cid for cid, info in dados.items()}

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        cliente_sel_nome = st.selectbox(
            "Cliente", list(nomes_clientes.keys()), key="ck_edit_cliente"
        )
    with col_e2:
        modulo_sel = st.selectbox("Módulo", MODULOS_CHECKLIST, key="ck_edit_modulo")

    cliente_sel_id = nomes_clientes[cliente_sel_nome]
    row_atual = dados[cliente_sel_id]["modulos"].get(modulo_sel)
    status_atual = row_atual["status"] if row_atual else "ok"

    # Mostrar status atual com cor
    cor_atual = CORES_CHECKLIST[status_atual]
    icone_atual = ICONES_CHECKLIST[status_atual]
    st.markdown(
        f'Status atual: <span style="background:{cor_atual}22;color:{cor_atual};'
        f'padding:3px 10px;border-radius:8px;font-weight:600">'
        f'{icone_atual} {_LABEL_STATUS[status_atual]}</span>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    opcoes = [_LABEL_STATUS[s] for s in STATUS_CHECKLIST]
    novo_label = st.radio(
        "Novo status",
        opcoes,
        index=STATUS_CHECKLIST.index(status_atual),
        horizontal=True,
        key="ck_edit_radio",
    )
    novo_status = STATUS_CHECKLIST[opcoes.index(novo_label)]

    # Vincular chamado se for problema
    chamado_vinculado = None
    if novo_status == "problema":
        chamados_cliente = [
            c for c in chamados_abertos
            if c["cliente_id"] == cliente_sel_id and c["categoria"] == modulo_sel
        ]
        if chamados_cliente:
            opts = ["Nenhum"] + [f"#{c['id']} — {c['titulo']}" for c in chamados_cliente]
            sel = st.selectbox("Vincular a chamado existente", opts, key="ck_edit_chamado")
            if sel != "Nenhum":
                idx = opts.index(sel) - 1
                chamado_vinculado = chamados_cliente[idx]["id"]

    if st.button("💾 Salvar alteração", type="primary", key="ck_salvar"):
        atualizar_status_modulo(cliente_sel_id, modulo_sel, novo_status, chamado_vinculado)
        adicionar_mensagem(
            "sucesso",
            f"{modulo_sel} de {cliente_sel_nome}: {_LABEL_STATUS[status_atual]} → {_LABEL_STATUS[novo_status]}",
        )
        st.rerun()
