"""Validações rápidas do banco `gestao.db` — imprime contagens por tabela."""
import sqlite3
import sys

DB = 'gestao.db'

def main():
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
    except Exception as e:
        print(f"Erro abrindo {DB}: {e}")
        sys.exit(1)

    tables = ['clientes','chamados','cobrancas','checklist']
    for t in tables:
        try:
            c = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception as e:
            c = f"erro: {e}"
        print(f"{t}: {c}")

    conn.close()


if __name__ == '__main__':
    main()
