import streamlit as st
from datetime import date
from src.database.operations import (
    listar_cobrancas_por_chamado,
    adicionar_cobranca,
    marcar_respondido,
    excluir_cobranca,
)
from src.utils.helpers import formatar_data_br, cobranca_atrasada, adicionar_mensagem


def renderizar_cobrancas(chamado_id: int, responsabilidade: str):
    cobrancas = listar_cobrancas_por_chamado(chamado_id)

    st.markdown("#### Cobranças ao cliente")

    if not cobrancas:
        if responsabilidade == "Cliente":
            st.caption("Nenhuma cobrança registrada ainda.")
        else:
            st.caption("Chamado de responsabilidade interna — cobranças não aplicáveis.")
    else:
        for cob in cobrancas:
            _renderizar_card_cobranca(cob)

    if responsabilidade == "Cliente":
        _renderizar_form_nova_cobranca(chamado_id)


def _renderizar_card_cobranca(cob):
    respondido = bool(cob["respondido"])
    atrasado = not respondido and cobranca_atrasada(cob["data_envio"])

    css_class = "respondido" if respondido else ("atrasado" if atrasado else "")
    icone = "✅" if respondido else ("⏰" if atrasado else "📤")

    with st.container():
        st.markdown(
            f'<div class="cobranca-card {css_class}">',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                f"{icone} **Enviado em {formatar_data_br(cob['data_envio'])}**"
                + (" — ⚠️ Sem resposta há mais de 3 dias" if atrasado else ""),
                unsafe_allow_html=True,
            )
            st.markdown(f"📝 {cob['mensagem']}")

            if respondido:
                st.markdown(
                    f"💬 **Resposta ({formatar_data_br(cob['data_resposta'])}):** {cob['resposta_cliente']}"
                )

        with col2:
            if not respondido:
                if st.button("Marcar respondido", key=f"resp_btn_{cob['id']}", use_container_width=True):
                    st.session_state[f"respondendo_{cob['id']}"] = True

            if st.button("🗑", key=f"del_cob_{cob['id']}", help="Excluir cobrança"):
                excluir_cobranca(cob["id"])
                adicionar_mensagem("aviso", "Cobrança excluída.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get(f"respondendo_{cob['id']}"):
        with st.form(f"form_resposta_{cob['id']}"):
            resposta = st.text_area("Resposta do cliente *", height=80)
            data_resp = st.date_input("Data da resposta", value=date.today())
            col_s, col_c = st.columns(2)
            with col_s:
                if st.form_submit_button("✅ Confirmar", type="primary"):
                    if not resposta.strip():
                        st.error("Informe a resposta do cliente.")
                    else:
                        marcar_respondido(cob["id"], resposta, data_resp)
                        st.session_state.pop(f"respondendo_{cob['id']}", None)
                        adicionar_mensagem("sucesso", "Resposta registrada. Status atualizado para 'Respondido'.")
                        st.rerun()
            with col_c:
                if st.form_submit_button("Cancelar"):
                    st.session_state.pop(f"respondendo_{cob['id']}", None)
                    st.rerun()

    st.markdown("---")


def _renderizar_form_nova_cobranca(chamado_id: int):
    chave = f"nova_cob_{chamado_id}"
    if st.button("📤 Registrar nova cobrança", key=f"btn_nova_cob_{chamado_id}"):
        st.session_state[chave] = True

    if st.session_state.get(chave):
        with st.form(f"form_nova_cob_{chamado_id}"):
            st.markdown("**Nova cobrança ao cliente**")
            mensagem = st.text_area(
                "Mensagem enviada ao cliente *",
                placeholder="Descreva o que foi solicitado ao cliente...",
                height=100,
            )
            data_envio = st.date_input("Data do envio", value=date.today())
            col_s, col_c = st.columns(2)
            with col_s:
                if st.form_submit_button("Registrar", type="primary"):
                    if not mensagem.strip():
                        st.error("Informe a mensagem enviada.")
                    else:
                        adicionar_cobranca(chamado_id, mensagem, data_envio)
                        st.session_state.pop(chave, None)
                        adicionar_mensagem(
                            "sucesso",
                            "Cobrança registrada. Status atualizado para 'Aguardando cliente'."
                        )
                        st.rerun()
            with col_c:
                if st.form_submit_button("Cancelar"):
                    st.session_state.pop(chave, None)
                    st.rerun()
