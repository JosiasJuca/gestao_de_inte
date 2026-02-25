"""Inspeciona colunas da tabela `clientes` em dois bancos: fonte e alvo (`gestao.db`).

Uso:
    python -m src.scripts.inspect_clientes_columns --source "src/components/integracoes (7).db"
"""
import argparse
import sqlite3
import sys


def cols(db_path, table='clientes'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(f"PRAGMA table_info({table})")
        rows = cur.fetchall()
    except Exception as e:
        conn.close()
        return None, str(e)
    conn.close()
    return [r[1] for r in rows], None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True)
    args = p.parse_args()

    src_cols, err = cols(args.source)
    if err:
        print(f"Erro lendo fonte: {err}")
    else:
        print(f"Colunas em fonte ({args.source}): {src_cols}")

    tgt_cols, err2 = cols('gestao.db')
    if err2:
        print(f"Erro lendo gestao.db: {err2}")
    else:
        print(f"Colunas em gestao.db: {tgt_cols}")


if __name__ == '__main__':
    main()
