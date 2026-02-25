import streamlit as st
from datetime import date, datetime
from src.database.operations import (
    listar_clientes,
    listar_chamados_abertos,
    listar_chamados_resolvidos,
    adicionar_chamado,
    atualizar_chamado,
    resolver_chamado,
    excluir_chamado,
)
from src.utils.constants import (
    STATUS_CHAMADO,
    CATEGORIAS,
    RESPONSABILIDADE,
    RESPONSAVEIS,
)
from src.utils.helpers import (
    status_badge,
    responsabilidade_badge,
    formatar_data_br,
    calcular_dias_aberto,
    cor_dias_aberto,
    adicionar_mensagem,
    exibir_mensagens_persistentes,
)
from src.components.cobrancas import renderizar_cobrancas


def renderizar_chamados():
    exibir_mensagens_persistentes()

    aba_abertos, aba_resolvidos, aba_novo = st.tabs([
        "📋 Abertos", "✅ Resolvidos", "➕ Novo chamado"
    ])

    with aba_abertos:
        _renderizar_lista_abertos()

    with aba_resolvidos:
        _renderizar_lista_resolvidos()

    with aba_novo:
        _renderizar_form_novo_chamado()


def _renderizar_lista_abertos():
    chamados = listar_chamados_abertos()

    if not chamados:
        st.info("Nenhum chamado aberto no momento.")
        return

    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        busca = st.text_input("🔍 Buscar cliente", key="filtro_busca_abertos", placeholder="Nome do cliente...")
    with col2:
        filtro_status = st.selectbox("Status", ["Todos"] + STATUS_CHAMADO[:-1], key="filtro_status_abertos")
    with col3:
        filtro_resp = st.selectbox("Responsável", ["Todos"] + RESPONSAVEIS, key="filtro_resp_abertos")
    with col4:
        filtro_respon = st.selectbox("Responsabilidade", ["Todas"] + RESPONSABILIDADE, key="filtro_respon_abertos")

    filtrados = _filtrar_chamados(chamados, busca, filtro_status, filtro_resp, filtro_respon)

    st.markdown(f"**{len(filtrados)} chamado(s)**")

    for ch in filtrados:
        _renderizar_card_chamado(ch, modo="aberto")


def _renderizar_lista_resolvidos():
    chamados = listar_chamados_resolvidos()

    if not chamados:
        st.info("Nenhum chamado resolvido encontrado.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        busca = st.text_input("🔍 Buscar cliente", key="filtro_busca_res", placeholder="Nome do cliente...")
    with col2:
        filtro_resp = st.selectbox("Responsável", ["Todos"] + RESPONSAVEIS, key="filtro_resp_res")
    with col3:
        filtro_cat = st.selectbox("Categoria", ["Todas"] + CATEGORIAS, key="filtro_cat_res")

    filtrados = [
        c for c in chamados
        if (not busca or busca.lower() in c["cliente_nome"].lower())
        and (filtro_resp == "Todos" or c["responsavel"] == filtro_resp)
        and (filtro_cat == "Todas" or c["categoria"] == filtro_cat)
    ]

    st.markdown(f"**{len(filtrados)} chamado(s) resolvido(s)**")

    for ch in filtrados:
        _renderizar_card_chamado(ch, modo="resolvido")


def _renderizar_card_chamado(ch, modo: str):
    dias = calcular_dias_aberto(ch["data_abertura"])
    css_dias = cor_dias_aberto(dias)

    titulo_exp = (
        f"#{ch['id']} · {ch['cliente_nome']} · {ch['titulo']} · "
        f"{ch['categoria']} · {ch['status']}"
    )

    with st.expander(titulo_exp, expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"**Cliente:** {ch['cliente_nome']}  \n"
                f"**Título:** {ch['titulo']}  \n"
                f"**Categoria:** {ch['categoria']}  \n"
                f"**Abertura:** {formatar_data_br(ch['data_abertura'])}"
            )
        with col2:
            st.markdown("**Status:**", unsafe_allow_html=True)
            st.markdown(status_badge(ch["status"]), unsafe_allow_html=True)
            st.markdown("**Responsabilidade:**", unsafe_allow_html=True)
            st.markdown(responsabilidade_badge(ch["responsabilidade"]), unsafe_allow_html=True)
            st.markdown(f"**Responsável:** {ch['responsavel']}")
        with col3:
            if modo == "aberto":
                st.markdown(
                    f'<span class="{css_dias}" style="font-size:28px">{dias}d</span> em aberto',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"**Resolvido em:** {formatar_data_br(ch['data_resolucao'])}")
                if ch["resolucao"]:
                    st.markdown(f"**Resolução:** {ch['resolucao']}")

        if ch["descricao"]:
            st.markdown(f"**Descrição:** {ch['descricao']}")

        st.markdown("---")

        if modo == "aberto":
            _renderizar_acoes_chamado(ch)
            st.markdown("---")
            renderizar_cobrancas(ch["id"], ch["responsabilidade"])


def _renderizar_acoes_chamado(ch):
    col_e, col_r, col_d = st.columns(3)

    chave_edit = f"editando_{ch['id']}"
    chave_resol = f"resolvendo_{ch['id']}"

    with col_e:
        if st.button("✏️ Editar", key=f"btn_edit_{ch['id']}"):
            st.session_state[chave_edit] = not st.session_state.get(chave_edit, False)
            st.session_state.pop(chave_resol, None)

    with col_r:
        if st.button("✅ Resolver", key=f"btn_resol_{ch['id']}", type="primary"):
            st.session_state[chave_resol] = not st.session_state.get(chave_resol, False)
            st.session_state.pop(chave_edit, None)

    with col_d:
        chave_del = f"confirm_del_{ch['id']}"
        if st.button("🗑 Excluir", key=f"btn_del_{ch['id']}"):
            st.session_state[chave_del] = True
        if st.session_state.get(chave_del):
            if st.button("⚠️ Confirmar exclusão", key=f"confirm2_del_{ch['id']}", type="secondary"):
                excluir_chamado(ch["id"])
                st.session_state.pop(chave_del, None)
                adicionar_mensagem("aviso", f"Chamado #{ch['id']} excluído.")
                st.rerun()

    if st.session_state.get(chave_edit):
        _renderizar_form_edicao(ch)

    if st.session_state.get(chave_resol):
        _renderizar_form_resolucao(ch)


def _renderizar_form_edicao(ch):
    with st.form(f"form_edit_{ch['id']}"):
        st.markdown("**Editar chamado**")
        titulo = st.text_input("Título", value=ch["titulo"])
        col1, col2 = st.columns(2)
        with col1:
            categoria = st.selectbox(
                "Categoria", CATEGORIAS,
                index=CATEGORIAS.index(ch["categoria"]) if ch["categoria"] in CATEGORIAS else 0,
            )
            responsabilidade = st.selectbox(
                "Responsabilidade", RESPONSABILIDADE,
                index=RESPONSABILIDADE.index(ch["responsabilidade"]) if ch["responsabilidade"] in RESPONSABILIDADE else 0,
            )
        with col2:
            status = st.selectbox(
                "Status", STATUS_CHAMADO[:-1],
                index=STATUS_CHAMADO.index(ch["status"]) if ch["status"] in STATUS_CHAMADO else 0,
            )
            responsavel = st.selectbox(
                "Responsável", RESPONSAVEIS,
                index=RESPONSAVEIS.index(ch["responsavel"]) if ch["responsavel"] in RESPONSAVEIS else 0,
            )
        descricao = st.text_area("Descrição", value=ch["descricao"] or "")
        # Data de abertura (permite ajustar a data ao editar)
        try:
            if isinstance(ch.get("data_abertura"), (date, datetime)):
                default_data = ch.get("data_abertura") if isinstance(ch.get("data_abertura"), date) else ch.get("data_abertura").date()
            else:
                default_data = datetime.strptime(str(ch.get("data_abertura"))[:10], "%Y-%m-%d").date()
        except Exception:
            default_data = date.today()

        data_abertura = st.date_input("Data de abertura", value=default_data, key=f"edit_data_{ch['id']}")

        col_s, col_c = st.columns(2)
        with col_s:
            if st.form_submit_button("💾 Salvar", type="primary"):
                if not titulo.strip():
                    st.error("Título é obrigatório.")
                else:
                    atualizar_chamado(
                        ch["id"],
                        observacao=titulo,
                        categoria=categoria,
                        status=status,
                        responsabilidade=responsabilidade,
                        responsavel=responsavel,
                        descricao=descricao,
                        data_abertura=str(data_abertura),
                    )
                    st.session_state.pop(f"editando_{ch['id']}", None)
                    adicionar_mensagem("sucesso", f"Chamado #{ch['id']} atualizado.")
                    st.rerun()
        with col_c:
            if st.form_submit_button("Cancelar"):
                st.session_state.pop(f"editando_{ch['id']}", None)
                st.rerun()


def _renderizar_form_resolucao(ch):
    with st.form(f"form_resol_{ch['id']}"):
        st.markdown("**Resolver chamado**")
        resolucao = st.text_area(
            "Como foi resolvido? *",
            placeholder="Descreva a solução aplicada...",
            height=100,
        )
        data_res = st.date_input("Data da resolução", value=date.today())
        col_s, col_c = st.columns(2)
        with col_s:
            if st.form_submit_button("✅ Confirmar resolução", type="primary"):
                if not resolucao.strip():
                    st.error("Informe como foi resolvido.")
                else:
                    resolver_chamado(ch["id"], resolucao, data_res)
                    st.session_state.pop(f"resolvendo_{ch['id']}", None)
                    adicionar_mensagem("sucesso", f"Chamado #{ch['id']} resolvido.")
                    st.rerun()
        with col_c:
            if st.form_submit_button("Cancelar"):
                st.session_state.pop(f"resolvendo_{ch['id']}", None)
                st.rerun()


def _renderizar_form_novo_chamado():
    clientes = listar_clientes()
    if not clientes:
        st.warning("Cadastre pelo menos um cliente antes de abrir chamados.")
        return

    nomes = [c["nome"] for c in clientes]
    ids = {c["nome"]: c["id"] for c in clientes}
    resp_por_id = {c["id"]: c["responsavel"] for c in clientes}

    with st.form("form_novo_chamado", clear_on_submit=True):
        st.markdown("**Novo chamado**")

        col1, col2 = st.columns(2)
        with col1:
            cliente_nome = st.selectbox("Cliente *", nomes)
            titulo = st.text_input("Título *", placeholder="Resumo curto do problema...")
            categoria = st.selectbox("Categoria *", CATEGORIAS)
        with col2:
            responsabilidade = st.selectbox("Responsabilidade *", RESPONSABILIDADE)
            status = st.selectbox("Status inicial", STATUS_CHAMADO[:-1])

        data_abertura = st.date_input("Data de abertura", value=date.today())
        descricao = st.text_area(
            "Descrição",
            placeholder="Descreva o problema em detalhes...",
            height=120,
        )

        if st.form_submit_button("Abrir chamado", type="primary", use_container_width=True):
            if not titulo.strip():
                st.error("Título é obrigatório.")
            else:
                cliente_id = ids[cliente_nome]
                responsavel_cliente = resp_por_id.get(cliente_id)
                adicionar_chamado(
                    cliente_id=cliente_id,
                    titulo=titulo,
                    categoria=categoria,
                    status=status,
                    responsabilidade=responsabilidade,
                    responsavel=responsavel_cliente,
                    descricao=descricao,
                    data_abertura=data_abertura,
                )
                adicionar_mensagem("sucesso", f"Chamado '{titulo}' aberto para {cliente_nome}.")
                st.rerun()


def _filtrar_chamados(chamados, busca, filtro_status, filtro_resp, filtro_respon):
    resultado = chamados
    if busca:
        resultado = [c for c in resultado if busca.lower() in c["cliente_nome"].lower()]
    if filtro_status != "Todos":
        resultado = [c for c in resultado if c["status"] == filtro_status]
    if filtro_resp != "Todos":
        resultado = [c for c in resultado if c["responsavel"] == filtro_resp]
    if filtro_respon != "Todas":
        resultado = [c for c in resultado if c["responsabilidade"] == filtro_respon]
    return resultado


def renderizar_form_rapido():
    clientes = listar_clientes()
    if not clientes:
        st.caption("Sem clientes cadastrados.")
        return

    nomes = [c["nome"] for c in clientes]
    ids = {c["nome"]: c["id"] for c in clientes}
    resp_por_id = {c["id"]: c["responsavel"] for c in clientes}

    with st.form("form_rapido", clear_on_submit=True):
        cliente_nome = st.selectbox("Cliente", nomes, key="rapido_cliente")
        titulo = st.text_input("Título *", placeholder="Resumo rápido...", key="rapido_titulo")
        col1, col2 = st.columns(2)
        with col1:
            categoria = st.selectbox("Categoria", CATEGORIAS, key="rapido_cat")
        with col2:
            responsabilidade = st.selectbox("Responsabilidade", RESPONSABILIDADE, key="rapido_resp")
        data_abertura = st.date_input("Data de abertura", value=date.today(), key="rapido_data_abertura")

        if st.form_submit_button("➕ Abrir", type="primary", use_container_width=True):
            if not titulo.strip():
                st.error("Título é obrigatório.")
            else:
                cliente_id = ids[cliente_nome]
                responsavel_cliente = resp_por_id.get(cliente_id)
                adicionar_chamado(
                    cliente_id=cliente_id,
                    titulo=titulo,
                    categoria=categoria,
                    status="Aberto",
                    responsabilidade=responsabilidade,
                    responsavel=responsavel_cliente,
                    descricao="",
                    data_abertura=data_abertura,
                )
                adicionar_mensagem("sucesso", f"Chamado '{titulo}' aberto.")
                st.rerun()
