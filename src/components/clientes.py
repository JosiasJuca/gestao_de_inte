import streamlit as st
from src.database.operations import listar_clientes, adicionar_cliente, atualizar_cliente, excluir_cliente
from src.utils.constants import RESPONSAVEIS, STATUS_IMPLANTACAO, CORES_STATUS_IMPLANTACAO
from src.utils.helpers import adicionar_mensagem


def renderizar_gestao_clientes():
    clientes = listar_clientes(apenas_ativos=False)

    with st.expander("➕ Novo cliente", expanded=False):
        with st.form("form_novo_cliente", clear_on_submit=True):
            nome = st.text_input("Nome do cliente *")
            responsavel = st.selectbox("Responsável *", RESPONSAVEIS)
            status_impl = st.selectbox("Status de implantação *", STATUS_IMPLANTACAO)
            if st.form_submit_button("Adicionar", type="primary"):
                if not nome.strip():
                    st.error("Nome é obrigatório.")
                else:
                    try:
                        adicionar_cliente(nome, responsavel, status_impl)
                        adicionar_mensagem("sucesso", f"Cliente '{nome}' adicionado.")
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE" in str(e):
                            st.error("Já existe um cliente com esse nome.")
                        else:
                            st.error(f"Erro: {e}")

    if not clientes:
        st.info("Nenhum cliente cadastrado ainda.")
        return

    st.markdown(f"**{len(clientes)} cliente(s) cadastrado(s)**")

    for c in clientes:
        status_label = "✓ Ativo" if c["ativo"] else "✗ Inativo"
        cor = "#198754" if c["ativo"] else "#dc3545"
        header = f"**{c['nome']}** — {c['responsavel']} &nbsp; <span style='color:{cor};font-size:12px'>{status_label}</span>"

        with st.expander(c["nome"], expanded=False):
            si_atual = c["status_implantacao"] if c["status_implantacao"] else "3. Novo cliente sem integração"
            cor_si = CORES_STATUS_IMPLANTACAO.get(si_atual, "#6c757d")
            st.markdown(
                header + f' &nbsp; <span style="background:{cor_si};color:white;font-size:11px;'
                f'font-weight:600;padding:2px 9px;border-radius:10px">{si_atual}</span>',
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Nome", value=c["nome"], key=f"nome_{c['id']}")
                novo_resp = st.selectbox(
                    "Responsável", RESPONSAVEIS,
                    index=RESPONSAVEIS.index(c["responsavel"]) if c["responsavel"] in RESPONSAVEIS else 0,
                    key=f"resp_{c['id']}"
                )
                novo_si = st.selectbox(
                    "Status de implantação",
                    STATUS_IMPLANTACAO,
                    index=STATUS_IMPLANTACAO.index(si_atual) if si_atual in STATUS_IMPLANTACAO else 0,
                    key=f"si_{c['id']}"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("💾 Salvar alterações", key=f"salvar_{c['id']}"):
                    try:
                        atualizar_cliente(c["id"], novo_nome, novo_resp, novo_si)
                        adicionar_mensagem("sucesso", "Cliente atualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

            if c["ativo"]:
                st.markdown("---")
                confirmar = st.checkbox(
                    "Confirmar desativação deste cliente",
                    key=f"conf_del_{c['id']}"
                )
                if confirmar:
                    if st.button("🗑 Desativar cliente", key=f"del_{c['id']}", type="secondary"):
                        excluir_cliente(c["id"])
                        adicionar_mensagem("aviso", f"Cliente '{c['nome']}' desativado.")
                        st.rerun()
