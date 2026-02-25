import os
import re
import streamlit as st
from typing import Optional, Dict

_IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "img")

_CSS = """
<style>
.regra-card {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 14px;
}
.regra-card h4 { margin: 0 0 8px 0; font-size: 15px; }
.passo-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px; height: 32px;
    border-radius: 50%;
    font-weight: 700;
    font-size: 15px;
    margin-right: 10px;
    flex-shrink: 0;
}
.passo-row {
    display: flex;
    align-items: flex-start;
    margin-bottom: 10px;
}
.passo-texto { padding-top: 4px; font-size: 14px; }
.faq-q { font-weight: 700; color: #1a1a2e; margin-top: 12px; }
.faq-a { color: #495057; margin-left: 12px; font-size: 14px; }
.alerta-regra {
    background: #fff3cd;
    border-left: 4px solid #e6a817;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 13px;
    margin: 10px 0;
}
.perigo-regra {
    background: #fde8e8;
    border-left: 4px solid #dc3545;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 13px;
    margin: 10px 0;
}
.tabela-regra { width: 100%; border-collapse: collapse; font-size: 13px; margin: 10px 0; }
.tabela-regra th { background: #f0f2f6; padding: 8px 12px; text-align: left; border: 1px solid #dee2e6; }
.tabela-regra td { padding: 8px 12px; border: 1px solid #dee2e6; }
.tabela-regra tr:nth-child(even) td { background: #f8f9fa; }
</style>
"""


def renderizar_regras():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.title("Regras e Passo a Passo")
    st.caption("Base de conhecimento do time de suporte de integrações.")

    tab_fluxo, tab_batidas, tab_colaboradores, tab_vendas = st.tabs([
        "Fluxo Geral",
        "Batidas",
        "Colaboradores",
        "Vendas",
    ])

    with tab_fluxo:
        _tab_fluxo()

    with tab_batidas:
        _tab_batidas()

    with tab_colaboradores:
        _tab_colaboradores()

    with tab_vendas:
        _tab_vendas()


# ─── FLUXO GERAL ──────────────────────────────────────────────────────────────

def _tab_fluxo():
    st.markdown("### Fluxo de Investigação")
    st.caption("Siga esta sequência ao analisar qualquer divergência de integração.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="regra-card" style="border-top:4px solid #0d6efd">'
            '<h4>1. Site do Cliente</h4>'
            '<p style="font-size:13px;color:#495057">Validar se a divergência existe na ponta — confirmar no portal/sistema do cliente antes de qualquer ação interna.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="regra-card" style="border-top:4px solid #198754">'
            '<h4>2. Servidor SFTP (FileZilla)</h4>'
            '<p style="font-size:13px;color:#495057">Verificar se o arquivo bruto chegou ao FileZilla. Se não chegou, o problema é no envio do cliente.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="regra-card" style="border-top:4px solid #e6a817">'
            '<h4>3. Conformidade do Arquivo</h4>'
            '<p style="font-size:13px;color:#495057">Comparar conteúdo do arquivo recebido com o registro esperado. Verificar formato, delimitador e campos obrigatórios.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    fluxo_path = os.path.join(_IMG_DIR, "fluxo.png")
    if os.path.exists(fluxo_path):
        st.markdown("**Diagrama de fluxo completo:**")
        st.image(fluxo_path, use_container_width=True)
    else:
        st.info("Imagem do fluxo não encontrada em `img/fluxo.png`.")


# ─── BATIDAS ──────────────────────────────────────────────────────────────────

def _tab_batidas():
    st.markdown("### Passo a Passo — Batidas de Ponto")

    # Checklist interativo
    st.markdown("#### Checklist de Auditoria")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.checkbox("Absenteísmo confirmado no Site do cliente", key="bat_1")
        st.checkbox("Arquivos presentes no FileZilla", key="bat_2")
    with col_c2:
        st.checkbox("Registro de ponto não encontrado no arquivo", key="bat_3")
        st.checkbox("PIS do colaborador conferido", key="bat_4")

    st.markdown("---")

    # Modelo de e-mail
    st.markdown("#### Modelo de Notificação ao Cliente")
    st.caption("Clique no ícone de copiar no canto do bloco para usar o template.")
    st.code(
        """Assunto: Moavi | [<Cliente>] | Batidas de ponto

Olá! Tudo bem?

Identificamos a falta de marcação de ponto para algumas filiais nos dias XXXXXXX.

Poderiam investigar o que causou esse problema de não envio das marcações de ponto, por favor?

Além disso, poderiam reenviar as marcações de ponto dos dias XXXX no modelo atual
da integração ou via AFD/AFDT, por favor?

Anexo modelo da integração.

Atenciosamente,""",
        language="text",
    )

    st.markdown("---")

    # Documentação visual
    st.markdown("#### Documentação Visual")
    img_cols = st.columns([1, 2, 2])
    imagens = [
        ("Caminho pasta FileZilla", "CaminhoPASTA.png"),
        ("Estrutura Moavi (CSV)", "ExpBATIDAS2.png"),
        ("Estrutura AFD (TXT)", "ExpBATIDAS_AFD.png"),
    ]
    for i, (label, fname) in enumerate(imagens):
        path = os.path.join(_IMG_DIR, fname)
        with img_cols[i]:
            st.markdown(f"**{label}**")
            if os.path.exists(path):
                st.image(path, use_container_width=True)
            else:
                st.caption(f"_(imagem `{fname}` não encontrada)_")

    st.markdown("---")

    # Parser AFD / AFDT
    st.markdown("#### Leitor de Linha AFD / AFDT-REP")
    st.caption("Cole uma linha do arquivo para identificar os campos automaticamente.")

    with st.expander("Como ler os campos", expanded=False):
        st.markdown(
            '<table class="tabela-regra">'
            "<thead><tr><th>Campo</th><th>Posição</th><th>Descrição</th></tr></thead>"
            "<tbody>"
            "<tr><td><strong>NSR</strong></td><td>0–9</td><td>Número sequencial do registro</td></tr>"
            "<tr><td><strong>Tipo</strong></td><td>9</td><td>Código de 1 dígito do tipo da linha</td></tr>"
            "<tr><td><strong>Data/Hora</strong></td><td>10–22</td><td>Compacto (DDMMYYYYHHMM) ou ISO (YYYY-MM-DDTHH:MM:SS)</td></tr>"
            "<tr><td><strong>PIS</strong></td><td>22–34 ou 35–46</td><td>Identificador do colaborador (10–12 dígitos)</td></tr>"
            "</tbody></table>",
            unsafe_allow_html=True,
        )

    linha_input = st.text_area(
        "Cole a linha AFD/AFDT aqui",
        height=90,
        key="parser_input",
        placeholder="000337857329012026103602036408079555280000000000000000",
    )

    col_v, _ = st.columns([1, 4])
    with col_v:
        validar = st.button("🔎 Analisar linha", type="primary", key="parser_btn")

    if validar:
        if not linha_input.strip():
            st.warning("Cole uma linha para analisar.")
        else:
            resultado = _parse_registro(linha_input.strip())
            if resultado.get("formato") == "desconhecido":
                st.error("Não foi possível identificar o formato da linha.")
                st.code(linha_input, language="text")
            else:
                st.success(f"Formato detectado: **{resultado['formato']}**")
                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                col_r1.metric("NSR", resultado.get("nsr", "—"))
                col_r2.metric("Tipo", resultado.get("tipo", "—"))
                col_r3.metric("Data / Hora", f"{resultado.get('data','—')} {resultado.get('hora','—')}")
                col_r4.metric("PIS", resultado.get("pis", "—"))


# ─── COLABORADORES ────────────────────────────────────────────────────────────

def _tab_colaboradores():
    st.markdown("### Fluxo de Atendimento — Colaboradores")

    st.markdown("#### 1. Integrações Essenciais (Dados de Novos Colaboradores)")
    st.markdown(
        '<div class="regra-card">'
        '<ul style="margin:0;font-size:14px">'
        '<li><strong>Formato:</strong> Arquivos recebidos exclusivamente em <strong>CSV</strong>.</li>'
        '<li><strong>Localização:</strong> Depositados na pasta <strong>"Importados"</strong>.</li>'
        '<li><strong>Identificação:</strong> A integração pode usar <strong>PIS</strong>, <strong>CPF</strong> ou <strong>Matrícula</strong> como chave.</li>'
        '<li><strong>Como analisar:</strong> Baixar o arquivo → abrir com delimitador → buscar colaborador para validar.</li>'
        '</ul>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 2. Fluxo de Investigação de Divergências")
    st.caption("Cenário: batida do colaborador não aparece.")

    st.markdown(
        '<table class="tabela-regra">'
        "<thead><tr><th>Cenário</th><th>Causa Identificada</th><th>Ação Necessária</th></tr></thead>"
        "<tbody>"
        "<tr><td>Colaborador <strong>não encontrado</strong></td><td>Não está cadastrado na escala</td><td>Ensinar o usuário a adicionar na escala.</td></tr>"
        "<tr><td>Colaborador <strong>cadastrado</strong></td><td>Escala com pessoa errada</td><td>Explicar que a escala está com a pessoa errada.</td></tr>"
        "<tr><td>Dados <strong>divergentes</strong></td><td>Dado diferente do real</td><td>Seguir para análise de PIS / Integração.</td></tr>"
        "</tbody></table>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### 3. Diagnóstico de PIS e Dados")

    st.markdown(
        '<div class="alerta-regra">'
        '⚠️ <strong>Ação padrão:</strong> Para qualquer erro de PIS ou ausência de dados, o contato deve ser feito com o <strong>RH do cliente</strong>.'
        '</div>',
        unsafe_allow_html=True,
    )

    casos = [
        ("🔴 PIS Diferente", "O PIS na integração não coincide com o informado.", "Pedir ao usuário para solicitar atualização do PIS no RH (sistema de ponto)."),
        ("🟡 PIS Zerado", "Campo de PIS vindo vazio ou zerado no CSV.", "Solicitar ao RH a correção do cadastro no sistema de origem."),
        ("⚪ Sem PIS / Dados Ausentes", "Não estamos recebendo os dados da pessoa no arquivo.", "Solicitar ao RH que inclua/envie o colaborador na próxima integração."),
    ]
    for titulo, causa, acao in casos:
        st.markdown(
            f'<div class="regra-card">'
            f'<h4>{titulo}</h4>'
            f'<p style="font-size:13px;color:#495057;margin:2px 0"><strong>Causa:</strong> {causa}</p>'
            f'<p style="font-size:13px;color:#0a6640;margin:2px 0"><strong>Ação:</strong> {acao}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### 4. FAQ — Colaboradores")
    faqs = [
        ("Podemos corrigir uma integração manualmente?",
         "Não. Nunca alteramos dados vindos de integração para evitar desalinhamento entre os sistemas."),
        ("Podemos corrigir dados do colaborador diretamente?",
         "Somente em casos onde não existe integração ativa. Se houver integração, a origem deve ser corrigida."),
        ("Para quem encaminhar casos críticos?",
         "Siga o fluxo da coluna 'Contato' na página de Integrações. Se não houver, acione: Ju, Madruga ou Edu."),
    ]
    for pergunta, resposta in faqs:
        st.markdown(
            f'<p class="faq-q">❓ {pergunta}</p>'
            f'<p class="faq-a">→ {resposta}</p>',
            unsafe_allow_html=True,
        )


# ─── VENDAS ───────────────────────────────────────────────────────────────────

def _tab_vendas():
    st.markdown("### Fluxo de Atendimento — Vendas")

    st.markdown("#### 1. Integrações Essenciais (Vendas)")
    st.markdown(
        '<div class="regra-card">'
        '<ul style="font-size:14px;margin:0">'
        '<li><strong>Granularidade:</strong> Curva de vendas enviada <strong>hora a hora</strong> e <strong>dia a dia</strong>.</li>'
        '<li><strong>Métricas obrigatórias:</strong> Faturamento (R$), Quantidade de cupons, Quantidade de itens.</li>'
        '<li><strong>Histórico inicial:</strong> Garantir envio do <strong>último mês completo</strong> para base de comparação.</li>'
        '</ul>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 2. Quebra por Setores (Departamentalização)")

    col_farm, col_super = st.columns(2)
    with col_farm:
        st.markdown(
            '<div class="regra-card" style="border-top:3px solid #0d6efd">'
            '<h4>🏥 Farmácia</h4>'
            '<p style="font-size:13px">Setores: <strong>Total, Balcão e Dermocosméticos</strong></p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col_super:
        st.markdown(
            '<div class="regra-card" style="border-top:3px solid #198754">'
            '<h4>🛒 Supermercado</h4>'
            '<p style="font-size:13px">Setores: <strong>Total, Padaria, FLV, Frios, Açougue, Adega</strong>, etc.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="perigo-regra">'
        '🚨 <strong>REGRA DE OURO:</strong> O cliente deve enviar o setor <strong>TOTAL separadamente</strong> no arquivo. '
        '<strong>Nunca somar cupons dos setores</strong> para chegar ao total — um único cupom pode conter itens de vários setores (geraria duplicidade).'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### 3. Exemplo de Layout do Arquivo de Vendas")

    vendas_path = os.path.join(_IMG_DIR, "vendas.png")
    if os.path.exists(vendas_path):
        st.image(vendas_path, use_container_width=True)
    else:
        st.caption("_(imagem `vendas.png` não encontrada)_")

    st.markdown("---")
    st.markdown("#### 4. Checklist de Validação do Arquivo")

    checks_vendas = [
        ("vend_1", "O delimitador do CSV está correto?"),
        ("vend_2", "O faturamento (R$) usa o formato decimal adequado?"),
        ("vend_3", "Existem registros para todas as horas do dia em que a loja esteve aberta?"),
        ("vend_4", "O campo 'Setor' identifica claramente o que é o 'Total'?"),
        ("vend_5", "O número de cupons do setor Total é coerente com o movimento da loja?"),
    ]
    for key, label in checks_vendas:
        st.checkbox(label, key=key)

    st.markdown("---")
    st.markdown("#### 5. FAQ — Vendas")
    faqs_vendas = [
        ("A soma dos setores não bate com o Total, o que fazer?",
         "Normal para Cupons. Mas faturamento (R$) e itens devem bater. Se não bater, pedir ao RH/TI do cliente para revisar a exportação."),
        ("O arquivo veio sem quebra hora a hora, podemos subir?",
         "Não. Sem a quebra horária o sistema não consegue gerar a curva de produtividade e a escala ficará comprometida."),
    ]
    for pergunta, resposta in faqs_vendas:
        st.markdown(
            f'<p class="faq-q">❓ {pergunta}</p>'
            f'<p class="faq-a">→ {resposta}</p>',
            unsafe_allow_html=True,
        )


# ─── Parser AFD / AFDT ────────────────────────────────────────────────────────

def _parse_afd_compacto(linha: str) -> Optional[Dict]:
    if len(linha) < 34:
        return None
    nsr  = linha[0:9]
    tipo = linha[9]
    data = linha[10:18]
    hora = linha[18:22]
    pis  = linha[22:34]
    if len(data) == 8:
        data_fmt = f"{data[6:8]}/{data[4:6]}/{data[0:4]}" if data.startswith(('19', '20')) else f"{data[0:2]}/{data[2:4]}/{data[4:]}"
    else:
        data_fmt = data
    hora_fmt = f"{hora[:2]}:{hora[2:]}" if len(hora) >= 4 else hora
    return {"nsr": nsr, "tipo": tipo, "data": data_fmt, "hora": hora_fmt, "pis": pis}


def _parse_afdt_iso(linha: str) -> Optional[Dict]:
    if not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", linha):
        return None
    try:
        nsr      = linha[0:9]
        tipo     = linha[9] if len(linha) > 9 else ""
        data_fmt = linha[10:20].replace("-", "/")
        hora_fmt = linha[21:26]
        pis      = linha[35:46] if len(linha) >= 46 else ""
        return {"nsr": nsr, "tipo": tipo, "data": data_fmt, "hora": hora_fmt, "pis": pis}
    except Exception:
        return None


def _parse_registro(linha: str) -> Dict:
    res = _parse_afdt_iso(linha)
    if res:
        return {"formato": "AFDT/ISO", **res}
    res = _parse_afd_compacto(linha)
    if res:
        return {"formato": "AFD compacto", **res}
    return {"formato": "desconhecido", "raw": linha}
