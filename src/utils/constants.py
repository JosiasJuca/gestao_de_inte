STATUS_IMPLANTACAO = [
    "1. Implantado com problema",
    "2. Implantado refazendo",
    "3. Novo cliente sem integração",
    "4. Implantado sem integração",
]

CORES_STATUS_IMPLANTACAO = {
    "1. Implantado com problema":    "#dc3545",
    "2. Implantado refazendo":       "#fd7e14",
    "3. Novo cliente sem integração": "#6c757d",
    "4. Implantado sem integração":  "#e6a817",
}

STATUS_CHAMADO = ["Aberto", "Em análise", "Aguardando cliente", "Respondido", "Resolvido"]

CATEGORIAS = ["Batida", "Escala", "Feriados", "Funcionários", "PDV", "Venda", "SSO"]

RESPONSABILIDADE = ["Interna", "Cliente"]

RESPONSAVEIS = ["Guilherme", "Eduardo", "Marcelo"]

MODULOS_CHECKLIST = ["Batida", "Escala", "Feriados", "Funcionários", "PDV", "Venda", "SSO"]

STATUS_CHECKLIST = ["ok", "problema", "construcao", "na"]

CORES_STATUS = {
    "Aberto": "#6c757d",
    "Em análise": "#0d6efd",
    "Aguardando cliente": "#e6a817",
    "Respondido": "#198754",
    "Resolvido": "#20c997",
}

CORES_RESPONSABILIDADE = {
    "Interna": "#0d6efd",
    "Cliente": "#fd7e14",
}

ICONES_CHECKLIST = {
    "ok": "✓",
    "problema": "✗",
    "construcao": "🛠",
    "na": "—",
}

CORES_CHECKLIST = {
    "ok": "#198754",
    "problema": "#dc3545",
    "construcao": "#0d6efd",
    "na": "#adb5bd",
}

CSS_STYLES = """
<style>
    /* Badges gerais */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        color: white;
    }
    /* Dias em aberto */
    .dias-verde  { color: #198754; font-weight: 700; }
    .dias-amarelo { color: #e6a817; font-weight: 700; }
    .dias-laranja { color: #fd7e14; font-weight: 700; }
    .dias-vermelho { color: #dc3545; font-weight: 700; }
    /* Card de cobrança */
    .cobranca-card {
        background: #f8f9fa;
        border-left: 4px solid #0d6efd;
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .cobranca-card.respondido {
        border-left-color: #198754;
    }
    .cobranca-card.atrasado {
        border-left-color: #dc3545;
    }
    /* Checklist grid */
    .checklist-header {
        font-weight: 700;
        font-size: 13px;
        text-align: center;
        padding: 4px;
        background: #f0f2f6;
        border-radius: 4px;
    }
    /* Métricas KPI */
    [data-testid="metric-container"] {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #e9ecef;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #f8f9fa;
    }
    /* Esconder botões de ancoragem */
    h1 a, h2 a, h3 a { display: none; }
</style>
"""
