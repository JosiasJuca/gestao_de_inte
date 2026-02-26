"""
Script de migração dos bancos antigos para gestao.db

bi_dash/integracoes.db:
  - clientes (49) → tabela clientes
  - chamados (141) → cada registro é um status de integração por módulo:
      status 1/2 (problema/refazendo) → checklist problema + chamado aberto
      status 3/5 (sem integração)     → checklist na
      status 6/7 (normal)             → checklist ok
      status 8 (em construção)        → checklist construcao

acompanhamento_chamados_/chamados.db:
  - chamados (5) → tabela chamados como chamados reais
"""

import sqlite3
import os
from datetime import date

# Caminhos
BASE = os.path.dirname(__file__)
DB_NOVO   = os.path.join(BASE, "gestao.db")
DB_BIDASH = r"c:/Users/Moavi J/Documents/bi_dash/integracoes.db"
DB_ACOMP  = r"c:/Users/Moavi J/Documents/acompanhamento_chamados_/chamados.db"


def conectar(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─── Mapeamentos ──────────────────────────────────────────────────────────────

def mapear_status_checklist(status_antigo: str) -> str:
    s = status_antigo.lower()
    if "1." in s or "problema" in s or "refazendo" in s or "2." in s:
        return "problema"
    if "construção" in s or "constru" in s or "8." in s:
        return "construcao"
    if "sem integração" in s or "sem integra" in s or "3." in s or "4." in s or "5." in s:
        return "na"
    return "ok"  # 6. / 7. Status Normal


def mapear_status_chamado(status_antigo: str, etapa: str, data_resolucao) -> str:
    if data_resolucao:
        return "Resolvido"
    etapa = (etapa or "").lower()
    if "aguardando cliente" in etapa:
        return "Aguardando cliente"
    if "andamento" in etapa or "teste" in etapa or "finalizar" in etapa:
        return "Em análise"
    return "Aberto"


def mapear_categoria(cat: str) -> str:
    validas = {"Batida", "Escala", "Feriados", "Funcionários", "PDV", "Venda", "SSO"}
    if cat in validas:
        return cat
    return ""


def normalizar_responsavel(resp: str) -> str:
    validos = {"Guilherme", "Eduardo", "Marcelo"}
    if resp in validos:
        return resp
    return "Guilherme"


# ─── Migração ─────────────────────────────────────────────────────────────────

def migrar():
    novo  = conectar(DB_NOVO)
    bi    = conectar(DB_BIDASH)
    acomp = conectar(DB_ACOMP)

    hoje = str(date.today())

    # ── 1. Limpar banco novo (recomeçar do zero) ──────────────────────────────
    novo.execute("PRAGMA foreign_keys = OFF")
    for tabela in ("cobrancas", "checklist", "chamados", "clientes"):
        novo.execute(f"DELETE FROM {tabela}")
        novo.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabela}'")
    novo.execute("PRAGMA foreign_keys = ON")
    novo.commit()
    print("Banco limpo.")

    # ── 2. Importar clientes do bi_dash ───────────────────────────────────────
    clientes_bi = bi.execute("SELECT * FROM clientes WHERE ativo=1 ORDER BY id").fetchall()
    mapa_id = {}  # old_id → new_id

    MODULOS = ["Batida", "Escala", "Feriados", "Funcionários", "PDV", "Venda", "SSO"]

    for c in clientes_bi:
        resp = normalizar_responsavel(c["classificacao"])
        cur = novo.execute(
            "INSERT OR IGNORE INTO clientes (nome, responsavel, ativo) VALUES (?, ?, 1)",
            (c["nome"], resp),
        )
        if cur.lastrowid == 0:
            row = novo.execute("SELECT id FROM clientes WHERE nome=?", (c["nome"],)).fetchone()
            mapa_id[c["id"]] = row["id"]
        else:
            mapa_id[c["id"]] = cur.lastrowid

        # Inicializa checklist com ok para todos os módulos
        for mod in MODULOS:
            novo.execute(
                "INSERT OR IGNORE INTO checklist (cliente_id, modulo, status) VALUES (?, ?, 'ok')",
                (mapa_id[c["id"]], mod),
            )

    novo.commit()
    print(f"  {len(clientes_bi)} clientes importados.")

    # ── 3. Processar chamados do bi_dash → checklist + chamados (problema) ────
    chamados_bi = bi.execute("SELECT * FROM chamados ORDER BY id").fetchall()
    n_checklist = 0
    n_chamados_bi = 0

    for ch in chamados_bi:
        old_cli = ch["cliente_id"]
        if old_cli not in mapa_id:
            continue

        new_cli = mapa_id[old_cli]
        status_raw = ch["status"] or ""
        categoria  = mapear_categoria(ch["categoria"] or "")
        ck_status  = mapear_status_checklist(status_raw)

        # Atualiza checklist
        if categoria in MODULOS:
            novo.execute(
                """UPDATE checklist SET status=?, atualizado_em=CURRENT_TIMESTAMP
                   WHERE cliente_id=? AND modulo=?""",
                (ck_status, new_cli, categoria),
            )
            n_checklist += 1

        # Só cria chamado real para os status de problema (1 ou 2)
        eh_problema = status_raw.startswith("1.") or status_raw.startswith("2.")
        if not eh_problema:
            continue

        etapa   = ch["etapa"] or ""
        obs     = ch["observacao"] or ""
        resoluc = ch["resolucao"] or ""
        data_ab = str(ch["data_abertura"])[:10] if ch["data_abertura"] else hoje
        data_re = str(ch["data_resolucao"])[:10] if ch["data_resolucao"] else None

        status_novo = mapear_status_chamado(status_raw, etapa, data_re)

        # Título: usa observação resumida ou padrão
        titulo_raw = obs.split("\n")[0][:80].strip() if obs else ""
        titulo = titulo_raw if titulo_raw else f"{categoria} — {status_raw[:30]}"

          cur2 = novo.execute(
                """INSERT INTO chamados
                    (cliente_id, observacao, categoria, status, responsabilidade, responsavel,
                     descricao, resolucao, data_abertura, data_resolucao)
                    VALUES (?, ?, ?, ?, 'Interna', ?, ?, ?, ?, ?)""",
                (new_cli, titulo, categoria, status_novo,
                 novo.execute("SELECT responsavel FROM clientes WHERE id=?", (new_cli,)).fetchone()["responsavel"],
                 obs, resoluc, data_ab, data_re),
          )
        chamado_id = cur2.lastrowid

        # Vincula checklist ao chamado
        if categoria in MODULOS and status_novo != "Resolvido":
            novo.execute(
                "UPDATE checklist SET chamado_id=? WHERE cliente_id=? AND modulo=?",
                (chamado_id, new_cli, categoria),
            )

        n_chamados_bi += 1

    novo.commit()
    print(f"  {n_checklist} entradas de checklist atualizadas.")
    print(f"  {n_chamados_bi} chamados de problema importados do bi_dash.")

    # ── 4. Importar chamados do acompanhamento_chamados_ ──────────────────────
    chamados_ac = acomp.execute("SELECT * FROM chamados ORDER BY id").fetchall()
    n_ac = 0
    n_cobrancas = 0

    for ch in chamados_ac:
        nome_cli = (ch["cliente"] or "").strip()
        if not nome_cli:
            continue

        # Busca cliente existente (case-insensitive, partial match)
        row_cli = novo.execute(
            "SELECT id, responsavel FROM clientes WHERE lower(nome) = lower(?)",
            (nome_cli,)
        ).fetchone()

        if not row_cli:
            # Tenta busca parcial
            row_cli = novo.execute(
                "SELECT id, responsavel FROM clientes WHERE lower(nome) LIKE lower(?)",
                (f"%{nome_cli}%",)
            ).fetchone()

        if not row_cli:
            # Cria novo cliente
            cur_cli = novo.execute(
                "INSERT INTO clientes (nome, responsavel, ativo) VALUES (?, 'Guilherme', 1)",
                (nome_cli,)
            )
            cli_id   = cur_cli.lastrowid
            cli_resp = "Guilherme"
            for mod in MODULOS:
                novo.execute(
                    "INSERT OR IGNORE INTO checklist (cliente_id, modulo, status) VALUES (?, ?, 'ok')",
                    (cli_id, mod),
                )
            print(f"    Novo cliente criado: {nome_cli}")
        else:
            cli_id   = row_cli["id"]
            cli_resp = row_cli["responsavel"]

        # Mapear status
        status_ac = ch["status"] or "Aguardando cliente"
        if "interno" in status_ac.lower() or "análise" in status_ac.lower():
            novo_status = "Em análise"
            responsabilidade = "Interna"
        elif "aguardando cliente" in status_ac.lower() or "cobrado" in (ch["etapa_atual"] or "").lower():
            novo_status = "Aguardando cliente"
            responsabilidade = "Cliente"
        elif "resolvido" in status_ac.lower():
            novo_status = "Resolvido"
            responsabilidade = "Interna"
        else:
            novo_status = "Aberto"
            responsabilidade = "Interna"

        obs_raw  = ch["observacao"] or ""
        resolucao = ch["resolucao"] or ""
        data_ab  = str(ch["data_abertura"])[:10] if ch["data_abertura"] else hoje
        data_re  = str(ch["data_resolucao"])[:10] if ch["data_resolucao"] else None
        cat_raw  = ch["categoria"] or ""

        # Categoria: tenta mapear para os módulos, senão Geral
        MAPA_CAT = {
            "arquivo": "",
            "arquivo incorreto": "",
            "arquivo não recebido": "",
        }
        categoria = MAPA_CAT.get(cat_raw.lower(), mapear_categoria(cat_raw))

        # Título: primeira linha da observação
        titulo_raw = obs_raw.split("\n")[0][:80].strip()
        titulo = titulo_raw if titulo_raw else (cat_raw[:80] if cat_raw else "Chamado importado")

          cur_ch = novo.execute(
                """INSERT INTO chamados
                    (cliente_id, observacao, categoria, status, responsabilidade, responsavel,
                     descricao, resolucao, data_abertura, data_resolucao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cli_id, titulo, categoria, novo_status, responsabilidade, cli_resp,
                 obs_raw, resolucao, data_ab, data_re),
          )
        chamado_id = cur_ch.lastrowid
        n_ac += 1

        # Se havia cobrança (etapa "Cobrado" e status "Aguardando cliente")
        etapa_ac = (ch["etapa_atual"] or "").lower()
        if responsabilidade == "Cliente" and ("cobrado" in etapa_ac or "aguardando" in status_ac.lower()):
            # Extrai a parte após "R:" da observação como mensagem da cobrança
            partes = obs_raw.split("\nR:")
            msg_cobranca = partes[0].strip() if partes else obs_raw
            data_envio = str(ch["atualizado_em"])[:10] if ch["atualizado_em"] else data_ab

            novo.execute(
                "INSERT INTO cobrancas (chamado_id, mensagem, data_envio) VALUES (?, ?, ?)",
                (chamado_id, msg_cobranca, data_envio),
            )
            n_cobrancas += 1

    novo.commit()
    print(f"  {n_ac} chamados importados do acompanhamento_chamados_.")
    print(f"  {n_cobrancas} cobranças criadas automaticamente.")

    # ── 5. Resumo ──────────────────────────────────────────────────────────────
    total_cli     = novo.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_ch      = novo.execute("SELECT COUNT(*) FROM chamados").fetchone()[0]
    total_ck      = novo.execute("SELECT COUNT(*) FROM checklist").fetchone()[0]
    total_cob     = novo.execute("SELECT COUNT(*) FROM cobrancas").fetchone()[0]

    novo.close()
    bi.close()
    acomp.close()

    print()
    print("=" * 40)
    print("Migração concluída!")
    print(f"  Clientes:   {total_cli}")
    print(f"  Chamados:   {total_ch}")
    print(f"  Checklist:  {total_ck}")
    print(f"  Cobranças:  {total_cob}")
    print("=" * 40)


if __name__ == "__main__":
    migrar()
