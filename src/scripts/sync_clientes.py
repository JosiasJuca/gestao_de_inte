"""Sincroniza clientes do DB fonte para o `gestao.db`.

Adiciona clientes ausentes e atualiza `responsavel` e `status_implantacao`
dos clientes já existentes (comparação por nome).

Uso:
    python -m src.scripts.sync_clientes --source "src/components/integracoes (7).db"
"""
import argparse
import sqlite3
import sys

from src.database import operations as ops


def get_val(r, keys, *names):
    for n in names:
        if n in keys:
            return r[n]
    return None


def sync(source_path):
    src_conn = sqlite3.connect(source_path)
    src_conn.row_factory = sqlite3.Row
    cur = src_conn.cursor()

    try:
        cur.execute("SELECT * FROM clientes")
    except sqlite3.OperationalError:
        print("Tabela 'clientes' não encontrada no DB fonte.")
        return 0, 0

    source_clients = cur.fetchall()

    target_clients = ops.listar_clientes(apenas_ativos=False)
    target_by_name = {c['nome']: c for c in target_clients}

    added = 0
    updated = 0
    details = []

    for r in source_clients:
        keys = r.keys()
        nome = get_val(r, keys, 'nome', 'nome_cliente')
        if not nome:
            continue
        responsavel = get_val(r, keys, 'responsavel', 'contato') or ''
        status_impl = get_val(r, keys, 'status_implantacao', 'status') or '3. Novo cliente sem integração'

        if nome in target_by_name:
            tc = target_by_name[nome]
            tc_id = tc['id']
            # Only update if different
            tc_responsavel = tc['responsavel'] if 'responsavel' in tc.keys() else ''
            tc_status = tc['status_implantacao'] if 'status_implantacao' in tc.keys() else ''
            if (tc_responsavel != responsavel) or (tc_status != status_impl):
                ops.atualizar_cliente(tc_id, nome, responsavel, status_impl)
                updated += 1
                details.append({'nome': nome, 'action': 'updated', 'id': tc_id})
        else:
            cid = ops.adicionar_cliente(nome, responsavel, status_impl)
            added += 1
            details.append({'nome': nome, 'action': 'added', 'id': cid})

    src_conn.close()
    print(f"Clientes adicionados: {added}")
    print(f"Clientes atualizados: {updated}")
    for d in details:
        print(f" - {d['action']}: {d['nome']} (id={d['id']})")
    return added, updated


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True)
    args = p.parse_args()
    try:
        sync(args.source)
    except Exception as e:
        print('Erro durante sincronização:', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
