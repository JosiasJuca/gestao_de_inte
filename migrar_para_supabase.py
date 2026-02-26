"""
Script de migração: copia todos os dados do gestao.db (SQLite) para o Supabase (PostgreSQL).
Execute uma única vez: python migrar_para_supabase.py
"""

import sqlite3
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "gestao.db")
DATABASE_URL = os.environ.get("DATABASE_URL")


def migrar():
    print("Conectando ao SQLite...")
    sqlite = sqlite3.connect(SQLITE_PATH)
    sqlite.row_factory = sqlite3.Row

    print("Conectando ao Supabase...")
    pg = psycopg2.connect(DATABASE_URL)
    cur = pg.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ── CLIENTES ──────────────────────────────────────────────────────────────
    clientes = sqlite.execute("SELECT * FROM clientes").fetchall()
    print(f"Migrando {len(clientes)} clientes...")
    for c in clientes:
        cur.execute("""
            INSERT INTO clientes (id, nome, responsavel, status_implantacao, ativo, criado_em, atualizado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (c["id"], c["nome"], c["responsavel"], c["status_implantacao"],
              c["ativo"], c["criado_em"], c["atualizado_em"]))

    # Sincroniza a sequence do SERIAL para continuar do ID correto
    cur.execute("SELECT setval('clientes_id_seq', (SELECT MAX(id) FROM clientes))")

    # ── CHAMADOS ──────────────────────────────────────────────────────────────
    chamados = sqlite.execute("SELECT * FROM chamados").fetchall()
    print(f"Migrando {len(chamados)} chamados...")
    for c in chamados:
        cur.execute("""
            INSERT INTO chamados (id, cliente_id, observacao, categoria, status, responsabilidade,
                                  responsavel, descricao, resolucao, data_abertura, data_resolucao,
                                  criado_em, atualizado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (c["id"], c["cliente_id"], c["observacao"], c["categoria"], c["status"],
              c["responsabilidade"], c["responsavel"], c["descricao"], c["resolucao"],
              c["data_abertura"], c["data_resolucao"], c["criado_em"], c["atualizado_em"]))

    cur.execute("SELECT setval('chamados_id_seq', (SELECT MAX(id) FROM chamados))")

    # ── COBRANÇAS ─────────────────────────────────────────────────────────────
    cobrancas = sqlite.execute("SELECT * FROM cobrancas").fetchall()
    print(f"Migrando {len(cobrancas)} cobranças...")
    for c in cobrancas:
        cur.execute("""
            INSERT INTO cobrancas (id, chamado_id, mensagem, data_envio, respondido,
                                   resposta_cliente, data_resposta, criado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (c["id"], c["chamado_id"], c["mensagem"], c["data_envio"], c["respondido"],
              c["resposta_cliente"], c["data_resposta"], c["criado_em"]))

    cur.execute("SELECT setval('cobrancas_id_seq', (SELECT MAX(id) FROM cobrancas))")

    # ── CHECKLIST ─────────────────────────────────────────────────────────────
    checklist = sqlite.execute("SELECT * FROM checklist").fetchall()
    print(f"Migrando {len(checklist)} entradas de checklist...")
    for c in checklist:
        cur.execute("""
            INSERT INTO checklist (id, cliente_id, modulo, status, chamado_id, atualizado_em)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (c["id"], c["cliente_id"], c["modulo"], c["status"],
              c["chamado_id"], c["atualizado_em"]))

    cur.execute("SELECT setval('checklist_id_seq', (SELECT MAX(id) FROM checklist))")

    pg.commit()
    pg.close()
    sqlite.close()
    print("\nMigração concluída com sucesso!")


if __name__ == "__main__":
    migrar()
