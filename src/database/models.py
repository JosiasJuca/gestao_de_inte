CRIAR_TABELAS = """
CREATE TABLE IF NOT EXISTS clientes (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                 TEXT NOT NULL UNIQUE,
    responsavel          TEXT NOT NULL,
    status_implantacao   TEXT NOT NULL DEFAULT '3. Novo cliente sem integração',
    ativo                INTEGER DEFAULT 1,
    criado_em            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chamados (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id       INTEGER NOT NULL REFERENCES clientes(id),
    observacao       TEXT NOT NULL,
    categoria        TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'Aberto',
    responsabilidade TEXT NOT NULL DEFAULT 'Interna',
    responsavel      TEXT NOT NULL,
    descricao        TEXT,
    resolucao        TEXT,
    data_abertura    DATE NOT NULL,
    data_resolucao   DATE,
    criado_em        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cobrancas (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    chamado_id       INTEGER NOT NULL REFERENCES chamados(id) ON DELETE CASCADE,
    mensagem         TEXT NOT NULL,
    data_envio       DATE NOT NULL,
    respondido       INTEGER DEFAULT 0,
    resposta_cliente TEXT,
    data_resposta    DATE,
    criado_em        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checklist (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id    INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    modulo        TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'ok',
    chamado_id    INTEGER REFERENCES chamados(id) ON DELETE SET NULL,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cliente_id, modulo)
);
"""

CRIAR_INDICES = """
CREATE INDEX IF NOT EXISTS idx_chamados_cliente     ON chamados(cliente_id);
CREATE INDEX IF NOT EXISTS idx_chamados_status      ON chamados(status);
CREATE INDEX IF NOT EXISTS idx_chamados_responsavel ON chamados(responsavel);
CREATE INDEX IF NOT EXISTS idx_chamados_abertura    ON chamados(data_abertura);
CREATE INDEX IF NOT EXISTS idx_cobrancas_chamado    ON cobrancas(chamado_id);
CREATE INDEX IF NOT EXISTS idx_checklist_cliente    ON checklist(cliente_id);
"""
