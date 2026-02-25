"""Limpa os dados principais do banco `gestao.db`.

Uso:
    python -m src.scripts.clear_data --yes

Sem `--yes` apenas mostra o que seria apagado.
"""
import argparse
import sqlite3
import sys

DB = 'gestao.db'
TABLES = ['cobrancas', 'checklist', 'chamados', 'clientes']


def preview():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for t in TABLES:
        try:
            c = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception as e:
            c = f"erro: {e}"
        print(f"{t}: {c}")
    conn.close()


def wipe():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    conn.execute("PRAGMA foreign_keys = OFF")
    for t in TABLES:
        try:
            cur.execute(f"DELETE FROM {t}")
            cur.execute("DELETE FROM sqlite_sequence WHERE name=?", (t,))
            print(f"Limpou tabela: {t}")
        except Exception as e:
            print(f"Erro ao limpar {t}: {e}")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--yes', action='store_true', help='Executa a limpeza')
    args = p.parse_args()

    print(f"DB alvo: {DB}")
    print("Contagens atuais:")
    preview()
    if not args.yes:
        print('\nRode com --yes para executar a limpeza.')
        return

    confirm = input('\nConfirma limpeza definitiva das tabelas acima? (sim/nao): ')
    if confirm.lower() not in ('s', 'sim', 'y', 'yes'):
        print('Aborted.')
        return

    wipe()
    print('\nApós limpeza:')
    preview()


if __name__ == '__main__':
    main()
