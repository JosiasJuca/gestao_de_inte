import os
import psycopg2
import psycopg2.extras
import psycopg2.pool
import streamlit as st
from contextlib import contextmanager
from datetime import date

from src.database.models import CRIAR_TABELAS, CRIAR_INDICES
from src.utils.constants import MODULOS_CHECKLIST, CATEGORIAS


@st.cache_resource
def _get_pool():
    return psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=os.environ.get("DATABASE_URL"),
    )


@contextmanager
def get_db():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def _exec(conn, sql, params=None):
    """Executa uma query usando RealDictCursor e retorna o cursor."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    return cur


def init_db():
    with get_db() as conn:
        for stmt in CRIAR_TABELAS:
            _exec(conn, stmt)
        for stmt in CRIAR_INDICES:
            _exec(conn, stmt)

        # Migração: adiciona coluna status_implantacao se ainda não existir
        col = _exec(
            conn,
            """SELECT column_name FROM information_schema.columns
               WHERE table_name = 'clientes' AND column_name = 'status_implantacao'"""
        )
        if not col.fetchone():
            _exec(
                conn,
                "ALTER TABLE clientes ADD COLUMN status_implantacao TEXT NOT NULL "
                "DEFAULT '3. Novo cliente sem integração'"
            )

        # Normaliza registros antigos
        _exec(
            conn,
            "UPDATE clientes SET status_implantacao = '3. Novo cliente sem integração' "
            "WHERE status_implantacao = 'Novo cliente'"
        )

        # Migração: renomear status 'Respondido' para 'Respondido - Em andamento'
        _exec(
            conn,
            "UPDATE chamados SET status = 'Respondido - Em andamento' WHERE status = 'Respondido'"
        )

        # Migração: renomear coluna 'titulo' para 'observacao' em chamados se necessário
        obs = _exec(
            conn,
            """SELECT column_name FROM information_schema.columns
               WHERE table_name = 'chamados' AND column_name = 'observacao'"""
        )
        tit = _exec(
            conn,
            """SELECT column_name FROM information_schema.columns
               WHERE table_name = 'chamados' AND column_name = 'titulo'"""
        )
        if not obs.fetchone() and tit.fetchone():
            _exec(conn, "ALTER TABLE chamados RENAME COLUMN titulo TO observacao")


# ─── CLIENTES ────────────────────────────────────────────────────────────────

def listar_clientes(apenas_ativos: bool = True):
    with get_db() as conn:
        if apenas_ativos:
            cur = _exec(conn, "SELECT * FROM clientes WHERE ativo=1 ORDER BY nome")
        else:
            cur = _exec(conn, "SELECT * FROM clientes ORDER BY nome")
        return cur.fetchall()


def adicionar_cliente(nome: str, responsavel: str, status_implantacao: str = "3. Novo cliente sem integração") -> int:
    with get_db() as conn:
        cur = _exec(
            conn,
            "INSERT INTO clientes (nome, responsavel, status_implantacao) VALUES (%s, %s, %s) RETURNING id",
            (nome.strip(), responsavel, status_implantacao),
        )
        cliente_id = cur.fetchone()["id"]
        for modulo in MODULOS_CHECKLIST:
            _exec(
                conn,
                "INSERT INTO checklist (cliente_id, modulo, status) VALUES (%s, %s, 'ok') ON CONFLICT DO NOTHING",
                (cliente_id, modulo),
            )
        return cliente_id


def atualizar_cliente(cliente_id: int, nome: str, responsavel: str, status_implantacao: str = "3. Novo cliente sem integração"):
    with get_db() as conn:
        _exec(
            conn,
            "UPDATE clientes SET nome=%s, responsavel=%s, status_implantacao=%s, atualizado_em=CURRENT_TIMESTAMP WHERE id=%s",
            (nome.strip(), responsavel, status_implantacao, cliente_id),
        )


def excluir_cliente(cliente_id: int):
    with get_db() as conn:
        _exec(conn, "UPDATE clientes SET ativo=0 WHERE id=%s", (cliente_id,))


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
        cur = _exec(
            conn,
            """INSERT INTO chamados
               (cliente_id, observacao, categoria, status, responsabilidade, responsavel, descricao, data_abertura)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (cliente_id, titulo.strip(), categoria, status, responsabilidade, responsavel,
             descricao, str(data_abertura)),
        )
        return cur.fetchone()["id"]


def listar_chamados_abertos():
    with get_db() as conn:
        cur = _exec(
            conn,
            """SELECT ch.*, cl.nome AS cliente_nome, cl.responsavel AS cliente_responsavel
               , ch.observacao AS titulo
               FROM chamados ch
               JOIN clientes cl ON cl.id = ch.cliente_id
               WHERE ch.status != 'Resolvido'
               ORDER BY ch.data_abertura ASC"""
        )
        return cur.fetchall()


def listar_chamados_resolvidos():
    with get_db() as conn:
        cur = _exec(
            conn,
            """SELECT ch.*, cl.nome AS cliente_nome, cl.responsavel AS cliente_responsavel
               , ch.observacao AS titulo
               FROM chamados ch
               JOIN clientes cl ON cl.id = ch.cliente_id
               WHERE ch.status = 'Resolvido'
               ORDER BY ch.data_resolucao DESC"""
        )
        return cur.fetchall()


def listar_todos_chamados():
    with get_db() as conn:
        cur = _exec(
            conn,
            """SELECT ch.*, cl.nome AS cliente_nome, cl.responsavel AS cliente_responsavel
               , ch.observacao AS titulo
               FROM chamados ch
               JOIN clientes cl ON cl.id = ch.cliente_id
               ORDER BY ch.data_abertura DESC"""
        )
        return cur.fetchall()


def atualizar_chamado(chamado_id: int, **campos):
    if not campos:
        return
    sets = ", ".join(f"{k}=%s" for k in campos)
    vals = list(campos.values()) + [chamado_id]
    with get_db() as conn:
        _exec(
            conn,
            f"UPDATE chamados SET {sets}, atualizado_em=CURRENT_TIMESTAMP WHERE id=%s",
            vals,
        )


def resolver_chamado(chamado_id: int, resolucao: str, data_resolucao=None):
    dr = str(data_resolucao or date.today())
    with get_db() as conn:
        _exec(
            conn,
            """UPDATE chamados
               SET status='Resolvido', resolucao=%s, data_resolucao=%s, atualizado_em=CURRENT_TIMESTAMP
               WHERE id=%s""",
            (resolucao, dr, chamado_id),
        )


def excluir_chamado(chamado_id: int):
    with get_db() as conn:
        _exec(conn, "DELETE FROM chamados WHERE id=%s", (chamado_id,))


def obter_estatisticas():
    with get_db() as conn:
        # Query 1: todos os contadores em uma única passagem pela tabela
        kpis = _exec(conn, """
            SELECT
                COUNT(*) FILTER (WHERE status != 'Resolvido')                                          AS total_abertos,
                COUNT(*) FILTER (WHERE status = 'Aguardando cliente')                                  AS aguardando_cliente,
                COUNT(*) FILTER (WHERE status = 'Resolvido' AND data_resolucao >= CURRENT_DATE - INTERVAL '30 days') AS resolvidos_30d,
                COUNT(*)                                                                                AS total_geral,
                COUNT(*) FILTER (WHERE status = 'Resolvido')                                           AS total_resolvidos
            FROM chamados
        """).fetchone()

        total_geral     = kpis["total_geral"]
        total_resolvidos = kpis["total_resolvidos"]
        taxa = round((total_resolvidos / total_geral * 100) if total_geral > 0 else 0, 1)

        # Query 2: agrupamentos por categoria, responsável e cliente em uma única passagem
        rows = _exec(conn, """
            SELECT
                ch.categoria,
                ch.responsavel,
                cl.nome AS cliente,
                ch.status
            FROM chamados ch
            JOIN clientes cl ON cl.id = ch.cliente_id
        """).fetchall()

        from collections import defaultdict
        cat_map  = defaultdict(int)
        resp_map = defaultdict(int)
        cli_map  = defaultdict(lambda: {"abertos": 0, "resolvidos": 0})

        for r in rows:
            if r["status"] != "Resolvido":
                cat_map[r["categoria"]] += 1
                resp_map[r["responsavel"]] += 1
                cli_map[r["cliente"]]["abertos"] += 1
            else:
                cli_map[r["cliente"]]["resolvidos"] += 1

        # Garantir que todas as categorias definidas em CATEGORIAS apareçam
        # no resultado, mesmo que tenham total 0.
        por_categoria  = [
            {"categoria": c, "total": int(cat_map.get(c, 0))}
            for c in CATEGORIAS
        ]
        por_categoria = sorted(por_categoria, key=lambda x: -x["total"])
        por_responsavel = sorted([{"responsavel": k, "total": v} for k, v in resp_map.items()], key=lambda x: -x["total"])
        por_cliente    = sorted([{"cliente": k, **v} for k, v in cli_map.items()],             key=lambda x: -(x["abertos"] + x["resolvidos"]))

        # Query 3: chamados abertos mais antigos (precisa de dados detalhados)
        mais_antigos = _exec(conn, """
            SELECT ch.id, ch.observacao AS titulo, ch.data_abertura, ch.status, ch.categoria,
                   ch.responsabilidade, ch.responsavel,
                   cl.nome AS cliente_nome,
                   cl.status_implantacao AS cliente_status_implantacao
            FROM chamados ch
            JOIN clientes cl ON cl.id = ch.cliente_id
            WHERE ch.status != 'Resolvido'
            ORDER BY ch.data_abertura ASC
        """).fetchall()

        # Query 4: cobranças atrasadas
        cobrancas_sem_resposta = _exec(conn, """
            SELECT COUNT(*) AS n FROM cobrancas
            WHERE respondido = 0
            AND data_envio::date <= CURRENT_DATE - INTERVAL '3 days'
        """).fetchone()["n"]

        return {
            "total_abertos":         kpis["total_abertos"],
            "aguardando_cliente":    kpis["aguardando_cliente"],
            "resolvidos_30d":        kpis["resolvidos_30d"],
            "taxa_resolucao":        taxa,
            "por_categoria":         por_categoria,
            "por_responsavel":       por_responsavel,
            "por_cliente":           por_cliente,
            "mais_antigos":          [dict(r) for r in mais_antigos],
            "cobrancas_sem_resposta": cobrancas_sem_resposta,
        }


# ─── COBRANÇAS ────────────────────────────────────────────────────────────────

def adicionar_cobranca(chamado_id: int, mensagem: str, data_envio) -> int:
    with get_db() as conn:
        cur = _exec(
            conn,
            "INSERT INTO cobrancas (chamado_id, mensagem, data_envio) VALUES (%s, %s, %s) RETURNING id",
            (chamado_id, mensagem.strip(), str(data_envio)),
        )
        cobranca_id = cur.fetchone()["id"]
        _exec(
            conn,
            "UPDATE chamados SET status='Aguardando cliente', atualizado_em=CURRENT_TIMESTAMP WHERE id=%s",
            (chamado_id,),
        )
        return cobranca_id


def listar_cobrancas_por_chamado(chamado_id: int):
    with get_db() as conn:
        cur = _exec(
            conn,
            "SELECT * FROM cobrancas WHERE chamado_id=%s ORDER BY data_envio ASC",
            (chamado_id,),
        )
        return cur.fetchall()


def marcar_respondido(cobranca_id: int, resposta: str, data_resposta=None):
    dr = str(data_resposta or date.today())
    with get_db() as conn:
        # Busca o chamado_id desta cobrança
        row = _exec(
            conn, "SELECT chamado_id FROM cobrancas WHERE id=%s", (cobranca_id,)
        ).fetchone()
        chamado_id = row["chamado_id"]

        # Marca a cobrança respondida
        _exec(
            conn,
            """UPDATE cobrancas
               SET respondido=1, resposta_cliente=%s, data_resposta=%s
               WHERE id=%s""",
            (resposta.strip(), dr, cobranca_id),
        )

        # Marca todas as cobranças pendentes do mesmo chamado como respondidas também
        _exec(
            conn,
            """UPDATE cobrancas
               SET respondido=1, resposta_cliente=%s, data_resposta=%s
               WHERE chamado_id=%s AND respondido=0""",
            (resposta.strip(), dr, chamado_id),
        )

        _exec(
            conn,
            "UPDATE chamados SET status='Respondido - Em andamento', atualizado_em=CURRENT_TIMESTAMP WHERE id=%s",
            (chamado_id,),
        )


def excluir_cobranca(cobranca_id: int):
    with get_db() as conn:
        _exec(conn, "DELETE FROM cobrancas WHERE id=%s", (cobranca_id,))


def listar_todas_cobrancas(apenas_pendentes: bool = False, cliente_id: int = None):
    where = []
    params = []

    if apenas_pendentes:
        where.append("cob.respondido = 0")

    if cliente_id:
        where.append("cl.id = %s")
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
            (CURRENT_DATE - cob.data_envio::date) AS dias_aguardando
        FROM cobrancas cob
        JOIN chamados ch ON ch.id = cob.chamado_id
        JOIN clientes cl ON cl.id = ch.cliente_id
        {clausula}
        ORDER BY cob.respondido ASC, cob.data_envio ASC
    """
    with get_db() as conn:
        cur = _exec(conn, sql, params if params else None)
        return cur.fetchall()


# ─── CHECKLIST ───────────────────────────────────────────────────────────────

def obter_checklist_completo():
    with get_db() as conn:
        cur = _exec(
            conn,
            """SELECT ck.*, cl.nome AS cliente_nome, cl.responsavel AS cliente_responsavel,
                      cl.status_implantacao AS cliente_status_implantacao
               FROM checklist ck
               JOIN clientes cl ON cl.id = ck.cliente_id
               WHERE cl.ativo = 1
               ORDER BY cl.nome, ck.modulo"""
        )
        return cur.fetchall()


def atualizar_status_modulo(cliente_id: int, modulo: str, status: str, chamado_id=None):
    with get_db() as conn:
        _exec(
            conn,
            """UPDATE checklist
               SET status=%s, chamado_id=%s, atualizado_em=CURRENT_TIMESTAMP
               WHERE cliente_id=%s AND modulo=%s""",
            (status, chamado_id, cliente_id, modulo),
        )


def obter_historico(data_inicio=None, data_fim=None, responsavel=None,
                    categoria=None, responsabilidade=None):
    where = ["ch.status = 'Resolvido'"]
    params = []
    if data_inicio:
        where.append("ch.data_resolucao >= %s")
        params.append(str(data_inicio))
    if data_fim:
        where.append("ch.data_resolucao <= %s")
        params.append(str(data_fim))
    if responsavel and responsavel != "Todos":
        where.append("ch.responsavel = %s")
        params.append(responsavel)
    if categoria and categoria != "Todas":
        where.append("ch.categoria = %s")
        params.append(categoria)
    if responsabilidade and responsabilidade != "Todas":
        where.append("ch.responsabilidade = %s")
        params.append(responsabilidade)

    sql = f"""
        SELECT ch.*, ch.observacao AS titulo, cl.nome AS cliente_nome,
               (ch.data_resolucao::date - ch.data_abertura::date) AS dias_resolucao
        FROM chamados ch
        JOIN clientes cl ON cl.id = ch.cliente_id
        WHERE {' AND '.join(where)}
        ORDER BY ch.data_resolucao DESC
    """
    with get_db() as conn:
        cur = _exec(conn, sql, params if params else None)
        return cur.fetchall()
