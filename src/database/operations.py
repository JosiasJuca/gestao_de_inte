import sqlite3
import os
from contextlib import contextmanager
from datetime import date

from src.database.models import CRIAR_TABELAS, CRIAR_INDICES
from src.utils.constants import MODULOS_CHECKLIST

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "gestao.db")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        for stmt in CRIAR_TABELAS.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        for stmt in CRIAR_INDICES.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        # Migração: adiciona coluna se banco já existia sem ela
        try:
            conn.execute(
                "ALTER TABLE clientes ADD COLUMN status_implantacao TEXT NOT NULL DEFAULT '3. Novo cliente sem integração'"
            )
        except Exception:
            pass  # coluna já existe
        # Normaliza registros antigos com valor simplificado
        conn.execute(
            "UPDATE clientes SET status_implantacao = '3. Novo cliente sem integração' "
            "WHERE status_implantacao = 'Novo cliente'"
        )

        # Migração: renomear coluna 'titulo' para 'observacao' em 'chamados' quando necessário
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(chamados)").fetchall()]
            if 'observacao' not in cols and 'titulo' in cols:
                # cria tabela temporária com novo esquema (observacao)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS chamados_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_id INTEGER NOT NULL REFERENCES clientes(id),
                        observacao TEXT NOT NULL,
                        categoria TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'Aberto',
                        responsabilidade TEXT NOT NULL DEFAULT 'Interna',
                        responsavel TEXT NOT NULL,
                        descricao TEXT,
                        resolucao TEXT,
                        data_abertura DATE NOT NULL,
                        data_resolucao DATE,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # copiar dados de titulo -> observacao
                conn.execute(
                    "INSERT INTO chamados_new (id, cliente_id, observacao, categoria, status, responsabilidade, responsavel, descricao, resolucao, data_abertura, data_resolucao, criado_em, atualizado_em) "
                    "SELECT id, cliente_id, titulo, categoria, status, responsabilidade, responsavel, descricao, resolucao, data_abertura, data_resolucao, criado_em, atualizado_em FROM chamados"
                )
                conn.execute("DROP TABLE chamados")
                conn.execute("ALTER TABLE chamados_new RENAME TO chamados")
        except Exception:
            pass


# ─── CLIENTES ────────────────────────────────────────────────────────────────

def listar_clientes(apenas_ativos: bool = True):
    with get_db() as conn:
        if apenas_ativos:
            return conn.execute(
                "SELECT * FROM clientes WHERE ativo=1 ORDER BY nome"
            ).fetchall()
        return conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()


def adicionar_cliente(nome: str, responsavel: str, status_implantacao: str = "3. Novo cliente sem integração") -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO clientes (nome, responsavel, status_implantacao) VALUES (?, ?, ?)",
            (nome.strip(), responsavel, status_implantacao),
        )
        cliente_id = cur.lastrowid
        for modulo in MODULOS_CHECKLIST:
            conn.execute(
                "INSERT OR IGNORE INTO checklist (cliente_id, modulo, status) VALUES (?, ?, 'ok')",
                (cliente_id, modulo),
            )
        return cliente_id


def atualizar_cliente(cliente_id: int, nome: str, responsavel: str, status_implantacao: str = "3. Novo cliente sem integração"):
    with get_db() as conn:
        conn.execute(
            "UPDATE clientes SET nome=?, responsavel=?, status_implantacao=?, atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
            (nome.strip(), responsavel, status_implantacao, cliente_id),
        )


def excluir_cliente(cliente_id: int):
    with get_db() as conn:
        conn.execute("UPDATE clientes SET ativo=0 WHERE id=?", (cliente_id,))


# ─── CHAMADOS ────────────────────────────────────────────────────────────────

def adicionar_chamado(
    cliente_id: int,
    titulo: str,
    categoria: str,
    status: str,
    responsabilidade: str,
    responsavel: str,
    descricao: str,
    data_abertura,
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO chamados
               (cliente_id, observacao, categoria, status, responsabilidade, responsavel, descricao, data_abertura)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (cliente_id, titulo.strip(), categoria, status, responsabilidade, responsavel,
             descricao, str(data_abertura)),
        )
        return cur.lastrowid


def listar_chamados_abertos():
    with get_db() as conn:
        return conn.execute(
            """SELECT ch.*, cl.nome AS cliente_nome, cl.responsavel AS cliente_responsavel
               , ch.observacao AS titulo
               FROM chamados ch
               JOIN clientes cl ON cl.id = ch.cliente_id
               WHERE ch.status != 'Resolvido'
               ORDER BY ch.data_abertura ASC"""
        ).fetchall()


def listar_chamados_resolvidos():
    with get_db() as conn:
        return conn.execute(
            """SELECT ch.*, cl.nome AS cliente_nome, cl.responsavel AS cliente_responsavel
               , ch.observacao AS titulo
               FROM chamados ch
               JOIN clientes cl ON cl.id = ch.cliente_id
               WHERE ch.status = 'Resolvido'
               ORDER BY ch.data_resolucao DESC"""
        ).fetchall()


def listar_todos_chamados():
    with get_db() as conn:
        return conn.execute(
            """SELECT ch.*, cl.nome AS cliente_nome, cl.responsavel AS cliente_responsavel
               , ch.observacao AS titulo
               FROM chamados ch
               JOIN clientes cl ON cl.id = ch.cliente_id
               ORDER BY ch.data_abertura DESC"""
        ).fetchall()


def atualizar_chamado(chamado_id: int, **campos):
    if not campos:
        return
    sets = ", ".join(f"{k}=?" for k in campos)
    vals = list(campos.values()) + [chamado_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE chamados SET {sets}, atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
            vals,
        )


def resolver_chamado(chamado_id: int, resolucao: str, data_resolucao=None):
    dr = str(data_resolucao or date.today())
    with get_db() as conn:
        conn.execute(
            """UPDATE chamados
               SET status='Resolvido', resolucao=?, data_resolucao=?, atualizado_em=CURRENT_TIMESTAMP
               WHERE id=?""",
            (resolucao, dr, chamado_id),
        )


def excluir_chamado(chamado_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM chamados WHERE id=?", (chamado_id,))


def obter_estatisticas():
    with get_db() as conn:
        total_abertos = conn.execute(
            "SELECT COUNT(*) FROM chamados WHERE status != 'Resolvido'"
        ).fetchone()[0]

        aguardando_cliente = conn.execute(
            "SELECT COUNT(*) FROM chamados WHERE status = 'Aguardando cliente'"
        ).fetchone()[0]

        resolvidos_30d = conn.execute(
            """SELECT COUNT(*) FROM chamados
               WHERE status = 'Resolvido'
               AND data_resolucao >= date('now', '-30 days')"""
        ).fetchone()[0]

        total_geral = conn.execute("SELECT COUNT(*) FROM chamados").fetchone()[0]
        total_resolvidos = conn.execute(
            "SELECT COUNT(*) FROM chamados WHERE status = 'Resolvido'"
        ).fetchone()[0]

        taxa = round((total_resolvidos / total_geral * 100) if total_geral > 0 else 0, 1)

        por_categoria = conn.execute(
            """SELECT categoria, COUNT(*) as total
               FROM chamados WHERE status != 'Resolvido'
               GROUP BY categoria ORDER BY total DESC"""
        ).fetchall()

        por_responsavel = conn.execute(
            """SELECT responsavel, COUNT(*) as total
               FROM chamados WHERE status != 'Resolvido'
               GROUP BY responsavel ORDER BY total DESC"""
        ).fetchall()

        por_cliente = conn.execute(
            """SELECT cl.nome AS cliente,
                       SUM(CASE WHEN ch.status != 'Resolvido' THEN 1 ELSE 0 END) AS abertos,
                       SUM(CASE WHEN ch.status = 'Resolvido' THEN 1 ELSE 0 END) AS resolvidos
               FROM chamados ch
               JOIN clientes cl ON cl.id = ch.cliente_id
               GROUP BY cl.nome
               ORDER BY (SUM(CASE WHEN ch.status != 'Resolvido' THEN 1 ELSE 0 END) +
                         SUM(CASE WHEN ch.status = 'Resolvido' THEN 1 ELSE 0 END)) DESC"""
        ).fetchall()

        mais_antigos = conn.execute(
            """SELECT ch.id, ch.observacao AS titulo, ch.data_abertura, ch.status, ch.categoria,
                      ch.responsabilidade, ch.responsavel,
                      cl.nome AS cliente_nome,
                      cl.status_implantacao AS cliente_status_implantacao
               FROM chamados ch
               JOIN clientes cl ON cl.id = ch.cliente_id
               WHERE ch.status != 'Resolvido'
               ORDER BY ch.data_abertura ASC"""
        ).fetchall()

        cobrancas_sem_resposta = conn.execute(
            """SELECT COUNT(*) FROM cobrancas
               WHERE respondido = 0
               AND date(data_envio) <= date('now', '-3 days')"""
        ).fetchone()[0]

        return {
            "total_abertos": total_abertos,
            "aguardando_cliente": aguardando_cliente,
            "resolvidos_30d": resolvidos_30d,
            "taxa_resolucao": taxa,
            "por_categoria": [dict(r) for r in por_categoria],
            "por_responsavel": [dict(r) for r in por_responsavel],
            "por_cliente": [dict(r) for r in por_cliente],
            "mais_antigos": [dict(r) for r in mais_antigos],
            "cobrancas_sem_resposta": cobrancas_sem_resposta,
        }


# ─── COBRANÇAS ────────────────────────────────────────────────────────────────

def adicionar_cobranca(chamado_id: int, mensagem: str, data_envio) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO cobrancas (chamado_id, mensagem, data_envio) VALUES (?, ?, ?)",
            (chamado_id, mensagem.strip(), str(data_envio)),
        )
        # Atualiza status do chamado para "Aguardando cliente"
        conn.execute(
            "UPDATE chamados SET status='Aguardando cliente', atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
            (chamado_id,),
        )
        return cur.lastrowid


def listar_cobrancas_por_chamado(chamado_id: int):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM cobrancas WHERE chamado_id=? ORDER BY data_envio ASC",
            (chamado_id,),
        ).fetchall()


def marcar_respondido(cobranca_id: int, resposta: str, data_resposta=None):
    dr = str(data_resposta or date.today())
    with get_db() as conn:
        conn.execute(
            """UPDATE cobrancas
               SET respondido=1, resposta_cliente=?, data_resposta=?
               WHERE id=?""",
            (resposta.strip(), dr, cobranca_id),
        )
        # Atualiza status do chamado para "Respondido"
        chamado_id = conn.execute(
            "SELECT chamado_id FROM cobrancas WHERE id=?", (cobranca_id,)
        ).fetchone()["chamado_id"]
        conn.execute(
            "UPDATE chamados SET status='Respondido', atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
            (chamado_id,),
        )


def excluir_cobranca(cobranca_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM cobrancas WHERE id=?", (cobranca_id,))


def listar_todas_cobrancas(apenas_pendentes: bool = False, cliente_id: int = None):
    where = []
    params = []

    if apenas_pendentes:
        where.append("cob.respondido = 0")

    if cliente_id:
        where.append("cl.id = ?")
        params.append(cliente_id)

    clausula = f"WHERE {' AND '.join(where)}" if where else ""

    sql = f"""
        SELECT
            cob.id,
            cob.chamado_id,
            cob.mensagem,
            cob.data_envio,
            cob.respondido,
            cob.resposta_cliente,
            cob.data_resposta,
            cob.criado_em,
            ch.observacao    AS chamado_titulo,
            ch.categoria     AS chamado_categoria,
            ch.status        AS chamado_status,
            cl.id            AS cliente_id,
            cl.nome          AS cliente_nome,
            cl.responsavel   AS cliente_responsavel,
            julianday('now') - julianday(cob.data_envio) AS dias_aguardando
        FROM cobrancas cob
        JOIN chamados ch ON ch.id = cob.chamado_id
        JOIN clientes cl ON cl.id = ch.cliente_id
        {clausula}
        ORDER BY cob.respondido ASC, cob.data_envio ASC
    """
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


# ─── CHECKLIST ───────────────────────────────────────────────────────────────

def obter_checklist_completo():
    with get_db() as conn:
        return conn.execute(
            """SELECT ck.*, cl.nome AS cliente_nome, cl.responsavel AS cliente_responsavel,
                      cl.status_implantacao AS cliente_status_implantacao
               FROM checklist ck
               JOIN clientes cl ON cl.id = ck.cliente_id
               WHERE cl.ativo = 1
               ORDER BY cl.nome, ck.modulo"""
        ).fetchall()


def atualizar_status_modulo(cliente_id: int, modulo: str, status: str, chamado_id=None):
    with get_db() as conn:
        conn.execute(
            """UPDATE checklist
               SET status=?, chamado_id=?, atualizado_em=CURRENT_TIMESTAMP
               WHERE cliente_id=? AND modulo=?""",
            (status, chamado_id, cliente_id, modulo),
        )


def obter_historico(data_inicio=None, data_fim=None, responsavel=None,
                    categoria=None, responsabilidade=None):
    where = ["ch.status = 'Resolvido'"]
    params = []
    if data_inicio:
        where.append("ch.data_resolucao >= ?")
        params.append(str(data_inicio))
    if data_fim:
        where.append("ch.data_resolucao <= ?")
        params.append(str(data_fim))
    if responsavel and responsavel != "Todos":
        where.append("ch.responsavel = ?")
        params.append(responsavel)
    if categoria and categoria != "Todas":
        where.append("ch.categoria = ?")
        params.append(categoria)
    if responsabilidade and responsabilidade != "Todas":
        where.append("ch.responsabilidade = ?")
        params.append(responsabilidade)

    sql = f"""
        SELECT ch.*, ch.observacao AS titulo, cl.nome AS cliente_nome,
               julianday(ch.data_resolucao) - julianday(ch.data_abertura) AS dias_resolucao
        FROM chamados ch
        JOIN clientes cl ON cl.id = ch.cliente_id
        WHERE {' AND '.join(where)}
        ORDER BY ch.data_resolucao DESC
    """
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()
