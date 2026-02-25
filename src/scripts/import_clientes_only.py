"""Importa apenas os clientes de um banco SQLite externo para o `gestao.db` do projeto.

Uso:
    python -m src.scripts.import_clientes_only --source "src/components/integracoes (7).db"

Evita duplicatas comparando pelo nome (campo `nome`).
"""
import argparse
import sqlite3
import sys

from src.database import operations as ops


def importar_clientes(source_path, dry_run=False):
    src_conn = sqlite3.connect(source_path)
    src_conn.row_factory = sqlite3.Row
    cur = src_conn.cursor()

    try:
        cur.execute("SELECT * FROM clientes")
    except sqlite3.OperationalError:
        print("Tabela 'clientes' não encontrada no DB fonte.")
        return

    existing = {c['nome'] for c in ops.listar_clientes(apenas_ativos=False)}
    added = []

    for r in cur.fetchall():
        keys = r.keys()
        nome = r['nome'] if 'nome' in keys else (r['nome_cliente'] if 'nome_cliente' in keys else None)
        responsavel = r['responsavel'] if 'responsavel' in keys else (r['contato'] if 'contato' in keys else '')
        if 'status_implantacao' in keys:
            status_impl = r['status_implantacao']
        elif 'status' in keys:
            status_impl = r['status']
        else:
            status_impl = '3. Novo cliente sem integração'
        if not nome:
            continue
        if nome in existing:
            continue
        if dry_run:
            print(f"[DRY] Criar cliente: {nome}")
            added.append({'nome': nome, 'id': None})
        else:
            cid = ops.adicionar_cliente(nome, responsavel or '', status_impl or '3. Novo cliente sem integração')
            print(f"Criado cliente: {nome} -> id {cid}")
            added.append({'nome': nome, 'id': cid})
            existing.add(nome)

    src_conn.close()
    print(f"Importação de clientes concluída. Total adicionados: {len(added)}")
    return added


def main():
    p = argparse.ArgumentParser(description="Importador de clientes do DB externo para gestao.db")
    p.add_argument("--source", required=True, help="Caminho para o arquivo SQLite fonte (.db)")
    p.add_argument("--dry-run", action="store_true", help="Executar sem gravar no DB alvo")
    args = p.parse_args()

    try:
        added = importar_clientes(args.source, dry_run=args.dry_run)
        if added is None:
            sys.exit(1)
    except Exception as e:
        print(f"Erro durante importação: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
