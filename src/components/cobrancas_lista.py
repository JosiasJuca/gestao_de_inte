import streamlit as st
from datetime import date
from src.database.operations import (
    listar_todas_cobrancas,
    marcar_respondido,
    excluir_cobranca,
    listar_clientes,
    listar_chamados_abertos,
    adicionar_cobranca,
)
from src.utils.constants import RESPONSAVEIS
from src.utils.helpers import formatar_data_br, adicionar_mensagem, exibir_mensagens_persistentes

_CSS = """
<style>
.dias-alerta { color: #dc3545; font-weight: 700; }
</style>
"""


def renderizar_cobrancas_lista():
    st.markdown(_CSS, unsafe_allow_html=True)
    exibir_mensagens_persistentes()

    col_titulo, col_btn = st.columns([5, 1])
    with col_titulo:
        st.markdown("### Cobranças ao cliente")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Nova cobrança", type="primary", use_container_width=True):
            st.session_state["nova_cob_modal"] = not st.session_state.get("nova_cob_modal", False)

    # ── Formulário de nova cobrança ────────────────────────────────────────────
    if st.session_state.get("nova_cob_modal"):
        _renderizar_form_nova_cobranca()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    todas = listar_todas_cobrancas()
    if not todas:
        st.info("Nenhuma cobrança registrada ainda. Clique em '➕ Nova cobrança' para começar.")
        return

    total = len(todas)
    pendentes = [c for c in todas if not c["respondido"]]
    atrasadas = [c for c in pendentes if (c["dias_aguardando"] or 0) > 3]
    respondidas = [c for c in todas if c["respondido"]]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total enviadas", total)
    with c2:
        st.metric("Aguardando resposta", len(pendentes))
    with c3:
        st.metric("Atrasadas (>3 dias)", len(atrasadas), delta="urgente" if atrasadas else None)
    with c4:
        st.metric("Respondidas", len(respondidas))

    st.markdown("---")

    # ── Filtros ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_vis = st.selectbox(
            "Exibir",
            ["Todas", "Apenas pendentes", "Apenas respondidas"],
            key="cob_lista_vis",
        )
    with col_f2:
        clientes = listar_clientes()
        nomes = ["Todos os clientes"] + [c["nome"] for c in clientes]
        filtro_cli = st.selectbox("Cliente", nomes, key="cob_lista_cli")
    with col_f3:
        filtro_resp = st.selectbox("Responsável", ["Todos"] + RESPONSAVEIS, key="cob_lista_resp")

    # Aplicar filtros
    exibir = list(todas)
    if filtro_vis == "Apenas pendentes":
        exibir = [c for c in exibir if not c["respondido"]]
    elif filtro_vis == "Apenas respondidas":
        exibir = [c for c in exibir if c["respondido"]]
    if filtro_cli != "Todos os clientes":
        exibir = [c for c in exibir if c["cliente_nome"] == filtro_cli]
    if filtro_resp != "Todos":
        exibir = [c for c in exibir if c["cliente_responsavel"] == filtro_resp]

    if not exibir:
        st.info("Nenhuma cobrança encontrada para os filtros selecionados.")
        return

    st.markdown(f"**{len(exibir)} cobrança(s)**")
    st.markdown("")

    # ── Agrupar: cliente → chamado → lista de cobranças ───────────────────────
    clientes_order = []
    por_cliente = {}
    for cob in exibir:
        cid = cob["cliente_id"]
        chid = cob["chamado_id"]
        if cid not in por_cliente:
            clientes_order.append(cid)
            por_cliente[cid] = {
                "nome": cob["cliente_nome"],
                "responsavel": cob["cliente_responsavel"],
                "chamados_order": [],
                "chamados": {},
            }
        cli = por_cliente[cid]
        if chid not in cli["chamados"]:
            cli["chamados_order"].append(chid)
            cli["chamados"][chid] = {
                "titulo": cob["chamado_titulo"],
                "categoria": cob["chamado_categoria"],
                "status": cob["chamado_status"],
                "cobrancas": [],
            }
        cli["chamados"][chid]["cobrancas"].append(cob)

    # ── Renderizar por cliente ─────────────────────────────────────────────────
    for cid in clientes_order:
        _renderizar_bloco_cliente(cid, por_cliente[cid])


def _renderizar_bloco_cliente(cid, cli):
    total_cob = sum(len(ch["cobrancas"]) for ch in cli["chamados"].values())
    n_pendentes = sum(
        1
        for ch in cli["chamados"].values()
        for cob in ch["cobrancas"]
        if not cob["respondido"]
    )

    badge_total = (
        f'<span style="background:#e2e3e5;color:#383d41;font-size:12px;font-weight:600;'
        f'padding:2px 10px;border-radius:10px">{total_cob} cobrança(s)</span>'
    )

    # Se houver cobranças respondidas E cobranças pendentes, mostrar "Em andamento"
    # Caso contrário, mostrar o número de pendentes (se houver).
    n_respondidas = total_cob - n_pendentes
    badge_status = ""
    if n_respondidas > 0 and n_pendentes > 0:
        # Em andamento: usar cor distinta (azul) para indicar progresso
        badge_status = (
            f'<span style="background:#0d6efd;color:white;font-size:12px;font-weight:600;'
            f'padding:2px 10px;border-radius:10px;margin-left:6px">⏳ Respondido - Em andamento</span>'
        )
    elif n_pendentes:
        # Pendentes continuam com estilo amarelo
        badge_status = (
            f'<span style="background:#fff3cd;color:#856404;font-size:12px;font-weight:600;'
            f'padding:2px 10px;border-radius:10px;margin-left:6px">⏳ {n_pendentes} pendente(s)</span>'
        )

    chave_exp = f"cob_cli_exp_{cid}"
    expandido = st.session_state.get(chave_exp, True)
    icone_toggle = "▲" if expandido else "▼"

    col_hdr, col_btn = st.columns([11, 1])
    with col_hdr:
        st.markdown(
            f'<div style="background:#e8eaf6;border-left:4px solid #3f51b5;padding:10px 16px;'
            f'border-radius:8px;margin-top:20px;margin-bottom:4px;display:flex;align-items:center;gap:10px">'
            f'<strong style="font-size:15px;color:#1a1a2e">👤 {cli["nome"]}</strong>'
            f'&nbsp;{badge_total}{badge_status}'
            f'<span style="margin-left:auto;font-size:12px;color:#555">{cli["responsavel"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        st.markdown("<div style='margin-top:22px'>", unsafe_allow_html=True)
        if st.button(icone_toggle, key=f"toggle_cli_{cid}", use_container_width=True, help="Expandir/Recolher"):
            st.session_state[chave_exp] = not expandido
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if expandido:
        for chid in cli["chamados_order"]:
            ch = cli["chamados"][chid]
            _renderizar_bloco_chamado(chid, ch)


def _renderizar_bloco_chamado(chid, ch):
    n = len(ch["cobrancas"])
    vezes_label = "1 vez" if n == 1 else f"{n} vezes"

    n_pendentes_ch = sum(1 for c in ch["cobrancas"] if not c["respondido"])
    cor_badge = "#dc3545" if n_pendentes_ch and n > 1 else "#fd7e14" if n_pendentes_ch else "#198754"

    st.markdown(
        f'<div style="background:#f8f9fa;border-left:3px solid #adb5bd;padding:8px 16px;'
        f'margin-left:16px;margin-bottom:4px;border-radius:6px;display:flex;align-items:center;gap:8px">'
        f'<span style="font-weight:700;color:#212529">#{chid} — {ch["titulo"]}</span>'
        f'<span style="font-size:12px;color:#6c757d">{ch["categoria"]}</span>'
        f'<span style="background:{cor_badge};color:white;font-size:11px;font-weight:700;'
        f'padding:2px 9px;border-radius:10px;margin-left:4px">cobrado {vezes_label}</span>'
        f'<span style="margin-left:auto;font-size:12px;color:#6c757d">{ch["status"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tem_respondida = any(c["respondido"] for c in ch["cobrancas"])
    for i, cob in enumerate(ch["cobrancas"], 1):
        _renderizar_item_cobranca(cob, i, n, tem_respondida)


def _renderizar_item_cobranca(cob, num, total, tem_respondida=False):
    respondido = bool(cob["respondido"])
    dias = int(cob["dias_aguardando"] or 0)
    atrasado = not respondido and dias > 3 and not tem_respondida

    if respondido:
        border_color = "#198754"
        estado = "✅ Respondida"
        bg_color = "#f8fffe"
    elif tem_respondida:
        border_color = "#adb5bd"
        estado = "— Encerrada sem resposta individual"
        bg_color = "#f8f9fa"
    elif atrasado:
        border_color = "#dc3545"
        estado = f"⚠️ Sem resposta há {dias} dias"
        bg_color = "#fff5f5"
    else:
        border_color = "#e6a817"
        estado = f"⏳ Aguardando há {dias} dia(s)"
        bg_color = "#fffdf5"

    ordinal = f"{num}ª cobrança"

    resposta_html = ""
    if respondido and cob["resposta_cliente"]:
        resposta_html = (
            f'<div style="font-size:13px;color:#0a6640;background:#f0fdf4;'
            f'padding:6px 10px;border-radius:5px;margin-top:6px">'
            f'💬 <strong>Resposta ({formatar_data_br(cob["data_resposta"])}):</strong> '
            f'{cob["resposta_cliente"]}</div>'
        )

    col_info, col_actions = st.columns([5, 1])

    with col_info:
        st.markdown(
            f'<div style="background:{bg_color};border:1px solid #e9ecef;'
            f'border-left:3px solid {border_color};border-radius:6px;'
            f'padding:10px 14px;margin-left:32px;margin-bottom:4px">'
            f'<div style="font-size:11px;font-weight:700;color:#6c757d;margin-bottom:6px">'
            f'<span style="background:#6c757d;color:white;padding:1px 7px;border-radius:8px;'
            f'font-size:10px;margin-right:6px">{ordinal}</span>'
            f'📅 {formatar_data_br(cob["data_envio"])} &nbsp;·&nbsp; {estado}'
            f'</div>'
            f'<div style="font-size:13px;color:#212529;background:#f8f9fa;'
            f'padding:6px 10px;border-radius:5px">'
            f'📤 {cob["mensagem"]}</div>'
            f'{resposta_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_actions:
        # Alinha os botões verticalmente
        st.markdown("<div style='margin-top:8px'>", unsafe_allow_html=True)
        if not respondido and not tem_respondida:
            if st.button(
                "✔ Respondido",
                key=f"cob_resp_{cob['id']}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state[f"resp_form_{cob['id']}"] = True
        if st.button("🗑", key=f"cob_del_{cob['id']}", use_container_width=True, help="Excluir"):
            excluir_cobranca(cob["id"])
            adicionar_mensagem("aviso", "Cobrança excluída.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Formulário de resposta (fora dos columns para não quebrar layout)
    if st.session_state.get(f"resp_form_{cob['id']}") and not tem_respondida:
        with st.form(f"form_resp_{cob['id']}"):
            st.markdown(
                f"**Registrar resposta — {cob['cliente_nome']}** "
                f"(#{cob['chamado_id']} {cob['chamado_titulo']})"
            )
            resposta = st.text_area(
                "O que o cliente respondeu? *",
                placeholder="Descreva a resposta do cliente...",
                height=80,
            )
            data_resp = st.date_input("Data da resposta", value=date.today())
            col_s, col_c = st.columns(2)
            with col_s:
                if st.form_submit_button("✅ Confirmar", type="primary"):
                    if not resposta.strip():
                        st.error("Informe a resposta.")
                    else:
                        marcar_respondido(cob["id"], resposta, data_resp)
                        st.session_state.pop(f"resp_form_{cob['id']}", None)
                        adicionar_mensagem(
                            "sucesso",
                            f"Resposta de {cob['cliente_nome']} registrada.",
                        )
                        st.rerun()
            with col_c:
                if st.form_submit_button("Cancelar"):
                    st.session_state.pop(f"resp_form_{cob['id']}", None)
                    st.rerun()


def _renderizar_form_nova_cobranca():
    chamados_abertos = listar_chamados_abertos()
    chamados_cliente = [c for c in chamados_abertos if c["responsabilidade"] == "Cliente"]

    with st.container():
        st.markdown(
            '<div style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px 20px;margin-bottom:16px">',
            unsafe_allow_html=True,
        )
        st.markdown("**📤 Nova cobrança ao cliente**")

        if not chamados_cliente:
            st.warning(
                "Não há chamados abertos com responsabilidade **Cliente**. "
                "Crie um chamado com responsabilidade 'Cliente' na aba Chamados primeiro."
            )
            if st.button("Fechar", key="fechar_nova_cob_vazio"):
                st.session_state.pop("nova_cob_modal", None)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            return

        with st.form("form_nova_cob_direto", clear_on_submit=True):
            opts_chamado = [
                f"#{c['id']} — {c['cliente_nome']} — {c['titulo']} ({c['categoria']})"
                for c in chamados_cliente
            ]
            sel = st.selectbox("Chamado *", opts_chamado)
            idx_sel = opts_chamado.index(sel)
            chamado_id = chamados_cliente[idx_sel]["id"]
            cliente_nome = chamados_cliente[idx_sel]["cliente_nome"]

            mensagem = st.text_area(
                "Mensagem enviada ao cliente *",
                placeholder="Descreva o que foi solicitado ao cliente...",
                height=100,
            )
            data_envio = st.date_input("Data do envio", value=date.today())

            col_s, col_c = st.columns(2)
            with col_s:
                if st.form_submit_button("Registrar cobrança", type="primary"):
                    if not mensagem.strip():
                        st.error("Informe a mensagem enviada.")
                    else:
                        adicionar_cobranca(chamado_id, mensagem, data_envio)
                        st.session_state.pop("nova_cob_modal", None)
                        adicionar_mensagem(
                            "sucesso",
                            f"Cobrança registrada para {cliente_nome}. Status do chamado atualizado para 'Aguardando cliente'.",
                        )
                        st.rerun()
            with col_c:
                if st.form_submit_button("Cancelar"):
                    st.session_state.pop("nova_cob_modal", None)
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
