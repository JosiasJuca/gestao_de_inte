"""Script de importação de um banco SQLite externo (ex: "integracoes (7).db").

Uso:
    python -m src.scripts.import_integracoes_db --source ".\caminho\para\integracoes (7).db"

O script mapeia clientes, chamados, cobranças e checklist do DB fonte
para o DB do projeto (`gestao.db`) usando as funções de `src.database.operations`.
"""
import argparse
import sqlite3
import sys
from datetime import datetime

from src.database import operations as ops


def row_get(r, key, default=None):
    try:
        return r[key]
    except Exception:
        return default


def importar(source_path, dry_run=False):
    src_conn = sqlite3.connect(source_path)
    src_conn.row_factory = sqlite3.Row
    cur = src_conn.cursor()

    # Cache clientes existentes no DB alvo
    existing = {c['nome']: c['id'] for c in ops.listar_clientes(apenas_ativos=False)}

    cliente_map = {}  # nome -> id alvo
    chamado_map = {}  # id_origem -> id_alvo

    # --- Clientes ---
    try:
        cur.execute("SELECT * FROM clientes")
    except sqlite3.OperationalError:
        print("Não há tabela 'clientes' no DB fonte. Pulando import de clientes.")
        cur_clients = []
    else:
        cur_clients = cur.fetchall()

    for r in cur_clients:
        nome = row_get(r, 'nome') or row_get(r, 'nome_cliente')
        responsavel = row_get(r, 'responsavel') or ''
        status_impl = row_get(r, 'status_implantacao') or '3. Novo cliente sem integração'
        if not nome:
            continue
        if nome in existing:
            cliente_id = existing[nome]
            print(f"Cliente existente: {nome} -> id {cliente_id}")
        else:
            if dry_run:
                cliente_id = None
                print(f"[DRY] Criar cliente: {nome}")
            else:
                cliente_id = ops.adicionar_cliente(nome, responsavel, status_impl)
                print(f"Criado cliente: {nome} -> id {cliente_id}")
            existing[nome] = cliente_id
        cliente_map[nome] = cliente_id

    # --- Chamados ---
    try:
        cur.execute("SELECT * FROM chamados")
    except sqlite3.OperationalError:
        print("Não há tabela 'chamados' no DB fonte. Pulando import de chamados.")
        cur_chamados = []
    else:
        cur_chamados = cur.fetchall()

    for r in cur_chamados:
        old_id = row_get(r, 'id')
        cliente_id_origem = row_get(r, 'cliente_id')
        # tenta obter nome do cliente pela FK
        cliente_nome = None
        if cliente_id_origem is not None:
            try:
                rc = src_conn.execute("SELECT nome FROM clientes WHERE id=?", (cliente_id_origem,)).fetchone()
                if rc:
                    cliente_nome = rc['nome']
            except Exception:
                cliente_nome = None

        if not cliente_nome:
            cliente_nome = row_get(r, 'cliente_nome') or row_get(r, 'nome_cliente')

        target_cliente_id = cliente_map.get(cliente_nome)
        if target_cliente_id is None:
            # cria cliente genérico se não existir
            if dry_run:
                print(f"[DRY] Criar cliente genérico para chamado {old_id}: {cliente_nome}")
                target_cliente_id = None
            else:
                target_cliente_id = ops.adicionar_cliente(cliente_nome or f"Cliente {old_id}", "", "3. Novo cliente sem integração")
                cliente_map[cliente_nome] = target_cliente_id

        titulo = row_get(r, 'titulo') or ''
        categoria = row_get(r, 'categoria') or ''
        status = row_get(r, 'status') or 'Aberto'
        responsabilidade = row_get(r, 'responsabilidade') or 'Interna'
        responsavel = row_get(r, 'responsavel') or ''
        descricao = row_get(r, 'descricao') or ''
        data_abertura = row_get(r, 'data_abertura') or row_get(r, 'created_at') or datetime.today().strftime('%Y-%m-%d')

        if dry_run:
            new_id = None
            print(f"[DRY] Inserir chamado '{titulo[:40]}' cliente='{cliente_nome}' status={status}")
        else:
            try:
                new_id = ops.adicionar_chamado(
                    target_cliente_id,
                    titulo,
                    categoria,
                    status,
                    responsabilidade,
                    responsavel,
                    descricao,
                    data_abertura,
                )
            except Exception as e:
                print(f"Erro ao inserir chamado {old_id}: {e}")
                continue

        chamado_map[old_id] = new_id

        # Se o chamado está resolvido no DB fonte, marca como resolvido
        if row_get(r, 'status') == 'Resolvido' or row_get(r, 'data_resolucao'):
            resolucao = row_get(r, 'resolucao') or ''
            data_resolucao = row_get(r, 'data_resolucao')
            if not dry_run and new_id:
                try:
                    ops.resolver_chamado(new_id, resolucao or '', data_resolucao)
                except Exception as e:
                    print(f"Erro ao marcar resolvido chamado {new_id}: {e}")

    # --- Cobrancas ---
    try:
        cur.execute("SELECT * FROM cobrancas")
    except sqlite3.OperationalError:
        print("Não há tabela 'cobrancas' no DB fonte. Pulando import de cobranças.")
        cur_cobs = []
    else:
        cur_cobs = cur.fetchall()

    for r in cur_cobs:
        old_chamado = row_get(r, 'chamado_id')
        msg = row_get(r, 'mensagem') or row_get(r, 'mensagem_cobranca') or ''
        data_envio = row_get(r, 'data_envio') or datetime.today().strftime('%Y-%m-%d')
        respondido = int(row_get(r, 'respondido') or 0)
        resposta_cliente = row_get(r, 'resposta_cliente') or ''
        data_resposta = row_get(r, 'data_resposta')

        target_chamado = chamado_map.get(old_chamado)
        if not target_chamado:
            print(f"Pulando cobrança ligada a chamado ausente (orig {old_chamado})")
            continue

        if dry_run:
            print(f"[DRY] Inserir cobranca para chamado {target_chamado}: respondido={respondido}")
            continue

        try:
            new_cob_id = ops.adicionar_cobranca(target_chamado, msg, data_envio)
            # restaurar status original do chamado, pois adicionar_cobranca seta 'Aguardando cliente'
            src_ch = None
            try:
                src_ch = src_conn.execute("SELECT status FROM chamados WHERE id=?", (old_chamado,)).fetchone()
            except Exception:
                src_ch = None
            if src_ch:
                orig_status = src_ch['status']
                ops.atualizar_chamado(target_chamado, status=orig_status)

            if respondido:
                ops.marcar_respondido(new_cob_id, resposta_cliente or '', data_resposta)
        except Exception as e:
            print(f"Erro ao inserir cobranca: {e}")

    # --- Checklist ---
    try:
        cur.execute("SELECT * FROM checklist")
    except sqlite3.OperationalError:
        print("Não há tabela 'checklist' no DB fonte. Pulando import de checklist.")
        cur_ck = []
    else:
        cur_ck = cur.fetchall()

    for r in cur_ck:
        cliente_id_origem = row_get(r, 'cliente_id')
        try:
            rc = src_conn.execute("SELECT nome FROM clientes WHERE id=?", (cliente_id_origem,)).fetchone()
            nome = rc['nome'] if rc else None
        except Exception:
            nome = None

        target_cliente_id = cliente_map.get(nome)
        modulo = row_get(r, 'modulo')
        status = row_get(r, 'status')
        chamado_origem = row_get(r, 'chamado_id')
        chamado_target = chamado_map.get(chamado_origem)

        if not target_cliente_id or not modulo:
            continue
        if dry_run:
            print(f"[DRY] Atualizar checklist cliente={nome} modulo={modulo} status={status}")
            continue
        try:
            ops.atualizar_status_modulo(target_cliente_id, modulo, status or 'ok', chamado_target)
        except Exception as e:
            print(f"Erro ao atualizar checklist: {e}")

    src_conn.close()

    print("Importação concluída.")


def main():
    p = argparse.ArgumentParser(description="Importador de .db de integrações para gestao.db")
    p.add_argument("--source", required=True, help="Caminho para o arquivo SQLite fonte (.db)")
    p.add_argument("--dry-run", action="store_true", help="Executar sem gravar no DB alvo")
    args = p.parse_args()

    try:
        importar(args.source, dry_run=args.dry_run)
    except Exception as e:
        print(f"Erro durante importação: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
