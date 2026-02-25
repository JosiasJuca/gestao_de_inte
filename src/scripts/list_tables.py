"""Lista as tabelas de um arquivo SQLite passado por `--source`."""
import argparse
import sqlite3
import sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True)
    args = p.parse_args()
    try:
        conn = sqlite3.connect(args.source)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        rows = [r[0] for r in cur.fetchall()]
        print('Tabelas:', rows)
        conn.close()
    except Exception as e:
        print('Erro:', e)
        sys.exit(1)

if __name__ == '__main__':
    main()
