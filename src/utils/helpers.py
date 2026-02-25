import streamlit as st
from datetime import date, datetime, timedelta
from src.utils.constants import CORES_STATUS, CORES_RESPONSABILIDADE


def status_badge(status: str) -> str:
    cor = CORES_STATUS.get(status, "#6c757d")
    return f'<span class="badge" style="background:{cor}">{status}</span>'


def responsabilidade_badge(resp: str) -> str:
    cor = CORES_RESPONSABILIDADE.get(resp, "#6c757d")
    return f'<span class="badge" style="background:{cor}">{resp}</span>'


def formatar_data_br(data_str) -> str:
    if not data_str:
        return "—"
    try:
        if isinstance(data_str, (date, datetime)):
            return data_str.strftime("%d/%m/%Y")
        d = str(data_str)[:10]
        ano, mes, dia = d.split("-")
        return f"{dia}/{mes}/{ano}"
    except Exception:
        return str(data_str)


def calcular_dias_aberto(data_abertura) -> int:
    try:
        if isinstance(data_abertura, (date, datetime)):
            d = data_abertura if isinstance(data_abertura, date) else data_abertura.date()
        else:
            d = datetime.strptime(str(data_abertura)[:10], "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return 0


def cor_dias_aberto(dias: int) -> str:
    if dias <= 3:
        return "dias-verde"
    elif dias <= 7:
        return "dias-amarelo"
    elif dias <= 14:
        return "dias-laranja"
    return "dias-vermelho"


def dias_badge_html(data_abertura) -> str:
    dias = calcular_dias_aberto(data_abertura)
    css = cor_dias_aberto(dias)
    label = f"{dias}d"
    return f'<span class="{css}">{label}</span>'


def cobranca_atrasada(data_envio, dias_limite: int = 3) -> bool:
    try:
        if isinstance(data_envio, (date, datetime)):
            d = data_envio if isinstance(data_envio, date) else data_envio.date()
        else:
            d = datetime.strptime(str(data_envio)[:10], "%Y-%m-%d").date()
        return (date.today() - d).days > dias_limite
    except Exception:
        return False


def adicionar_mensagem(tipo: str, texto: str):
    if "mensagens" not in st.session_state:
        st.session_state["mensagens"] = []
    st.session_state["mensagens"].append({"tipo": tipo, "texto": texto})


def exibir_mensagens_persistentes():
    mensagens = st.session_state.pop("mensagens", [])
    for m in mensagens:
        if m["tipo"] == "sucesso":
            st.success(m["texto"])
        elif m["tipo"] == "erro":
            st.error(m["texto"])
        elif m["tipo"] == "aviso":
            st.warning(m["texto"])
        else:
            st.info(m["texto"])
