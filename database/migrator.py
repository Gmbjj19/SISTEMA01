import json
import shutil
from datetime import datetime, date
from pathlib import Path
from config import DATABASE_PATH, LEGACY_FILES, LOGGER
from .connection import DatabaseManager, db_manager
from models.enums import TaskPriority, TaskStatus
from models.task import parse_date_str, format_date_iso

CREATE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    obra TEXT NOT NULL DEFAULT 'Geral',
    responsible TEXT NOT NULL DEFAULT 'Não Atribuído',
    start_date TEXT,
    end_date TEXT,
    priority TEXT NOT NULL DEFAULT 'Média',
    status TEXT NOT NULL DEFAULT 'Pendente',
    description TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_obra ON tasks(obra);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_end_date ON tasks(end_date);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);

CREATE TABLE IF NOT EXISTS concrete_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    boletim_code TEXT NOT NULL UNIQUE,
    obra TEXT NOT NULL,
    elemento TEXT NOT NULL,
    data_concretagem TEXT NOT NULL,
    fck_mpa INTEGER NOT NULL DEFAULT 30,
    slump_cm REAL NOT NULL DEFAULT 12.0,
    brita_tipo TEXT NOT NULL DEFAULT 'Brita 1',
    volume_teorico REAL NOT NULL DEFAULT 0.0,
    perda_percentual REAL NOT NULL DEFAULT 5.0,
    volume_total REAL NOT NULL DEFAULT 0.0,
    fornecedor TEXT DEFAULT '',
    nota_fiscal TEXT DEFAULT '',
    lacres TEXT DEFAULT '',
    corpos_prova INTEGER DEFAULT 4,
    responsavel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Concluído',
    observacoes TEXT DEFAULT '',
    itens_json TEXT DEFAULT '[]',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_concrete_obra ON concrete_measurements(obra);
CREATE INDEX IF NOT EXISTS idx_concrete_data ON concrete_measurements(data_concretagem);

CREATE TABLE IF NOT EXISTS quantitativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    disciplina TEXT NOT NULL DEFAULT 'Estrutural',
    obra TEXT NOT NULL,
    torre_setor TEXT NOT NULL,
    pavimento TEXT NOT NULL,
    folha_projeto TEXT DEFAULT '—',
    revisao TEXT NOT NULL DEFAULT 'R01',
    data_levantamento TEXT NOT NULL,
    responsavel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'finalizado',
    observacoes TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quant_obra ON quantitativos(obra);
CREATE INDEX IF NOT EXISTS idx_quant_pav ON quantitativos(pavimento);

CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quantitativo_id INTEGER NOT NULL,
    elemento TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'Bloco',
    local TEXT NOT NULL,
    pecas INTEGER NOT NULL DEFAULT 1,
    largura REAL NOT NULL DEFAULT 0.0,
    comprimento REAL NOT NULL DEFAULT 0.0,
    altura REAL NOT NULL DEFAULT 0.0,
    qtd REAL NOT NULL DEFAULT 1.0,
    concreto_m3 REAL NOT NULL DEFAULT 0.0,
    formas_m2 REAL NOT NULL DEFAULT 0.0,
    execucao TEXT NOT NULL DEFAULT 'Não executado',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quantitativo_id) REFERENCES quantitativos(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lanc_quant_id ON lancamentos(quantitativo_id);
"""

def init_database(manager: DatabaseManager = db_manager) -> None:
    """Cria tabelas e índices necessários caso não existam."""
    LOGGER.info("Inicializando schema do banco de dados em %s", manager.db_path)
    with manager.get_connection() as conn:
        conn.executescript(CREATE_SCHEMA_SQL)
    LOGGER.info("Schema do banco de dados verificado com sucesso.")

def migrate_legacy_data_if_needed(manager: DatabaseManager = db_manager) -> int:
    """
    Importa dados dos arquivos legados (.json) para o SQLite caso o banco esteja vazio.
    Preserva integridade e realiza backup dos arquivos importados.
    """
    with manager.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) as total FROM tasks").fetchone()["total"]
        if count > 0:
            LOGGER.info("Banco de dados já contém %d tarefas. Pulando migração legada.", count)
            return 0

    imported_total = 0
    seen_signatures = set()

    for legacy_file in LEGACY_FILES:
        if not legacy_file.exists():
            continue
        try:
            with open(legacy_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue
                raw_data = json.loads(content)

            if not isinstance(raw_data, list):
                continue

            for item in raw_data:
                if isinstance(item, str):
                    name = item.strip()
                    obra = "Geral"
                    resp = "Não Atribuído"
                    s_date = None
                    e_date = None
                    priority = TaskPriority.MEDIA.value
                    status = TaskStatus.PENDENTE.value
                    desc = ""
                elif isinstance(item, dict):
                    name = (item.get("name") or item.get("text") or "").strip()
                    if not name:
                        continue
                    obra = (item.get("obra") or "Geral").strip()
                    resp = (item.get("responsible") or "Não Atribuído").strip()
                    s_date = format_date_iso(parse_date_str(item.get("start_date")))
                    e_date = format_date_iso(parse_date_str(item.get("end_date")))
                    priority = item.get("priority", TaskPriority.MEDIA.value)
                    completed = item.get("completed", False)
                    status = TaskStatus.CONCLUIDA.value if completed else TaskStatus.PENDENTE.value
                    desc = item.get("description", "").strip()
                else:
                    continue

                sig = (name.lower(), obra.lower())
                if sig in seen_signatures:
                    continue
                seen_signatures.add(sig)

                with manager.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO tasks (name, obra, responsible, start_date, end_date, priority, status, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """, (name, obra, resp, s_date, e_date, priority, status, desc))
                imported_total += 1

            # Cria backup dos arquivos legados
            backup_path = legacy_file.with_suffix(".json.bak")
            if not backup_path.exists():
                shutil.copy(legacy_file, backup_path)
                LOGGER.info("Backup criado para arquivo legado: %s -> %s", legacy_file.name, backup_path.name)

        except Exception as e:
            LOGGER.warning("Falha ao analisar arquivo legado %s: %s", legacy_file, e)

    LOGGER.info("Migração concluída: %d tarefas migradas para SQLite.", imported_total)
    return imported_total

def seed_sample_quantitativos_if_needed(manager: DatabaseManager = db_manager) -> None:
    """Popula com o quantitativo da Fundação Chronos caso a tabela esteja vazia."""
    with manager.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM quantitativos").fetchone()["c"]
        if count > 0:
            return

        cursor = conn.execute("""
            INSERT INTO quantitativos (
                codigo, disciplina, obra, torre_setor, pavimento, folha_projeto,
                revisao, data_levantamento, responsavel, status, observacoes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            "QNT-CHRONOS-01",
            "Estrutural",
            "CHRONOS",
            "TORRE 01 E 02",
            "FUNDAÇÃO",
            "—",
            "R02",
            "2026-11-11",
            "Gil marcio Bispo de jesus junior",
            "finalizado",
            "Levantamento executivo de blocos e sapatas da fundação conforme projeto estrutural R02."
        ))
        quant_id = cursor.lastrowid

        # 15 Lançamentos idênticos ao projeto do usuário
        itens_sample = [
            ("B101", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 0.9, 0.9, 1.0, 1.0, 0.810, 3.60),
            ("B102", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 0.9, 0.9, 1.0, 1.0, 0.810, 3.60),
            ("B103", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 0.8, 0.8, 0.8, 1.0, 0.512, 2.56),
            ("B118", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 0.8, 0.8, 0.8, 1.0, 0.512, 2.56),
            ("B119", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 0.8, 0.8, 0.8, 1.0, 0.512, 2.56),
            ("B120", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 1.2, 1.2, 1.0, 1.0, 1.440, 4.80),
            ("B121", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 1.2, 1.2, 1.0, 1.0, 1.440, 4.80),
            ("B122", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 1.5, 1.5, 1.2, 1.0, 2.700, 7.20),
            ("B123", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 1.5, 1.5, 1.2, 1.0, 2.700, 7.20),
            ("B124", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 2.0, 2.0, 1.4, 1.0, 5.600, 11.20),
            ("B125", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 2.0, 2.0, 1.4, 1.0, 5.600, 11.20),
            ("B126", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 2.5, 2.5, 1.5, 1.0, 9.375, 15.00),
            ("B127", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 2.5, 2.5, 1.5, 1.0, 9.375, 15.00),
            ("B128", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 2.8, 2.8, 1.6, 1.0, 12.544, 17.92),
            ("B129", "Bloco", "TORRE 01 E 02 · FUNDAÇÃO", 1, 2.6, 2.6, 1.6, 1.0, 10.816, 51.88)
        ]

        for el, tp, loc, pc, l, c, h, q, v_conc, v_form in itens_sample:
            conn.execute("""
                INSERT INTO lancamentos (
                    quantitativo_id, elemento, tipo, local, pecas, largura,
                    comprimento, altura, qtd, concreto_m3, formas_m2, execucao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Não executado')
            """, (quant_id, el, tp, loc, pc, l, c, h, q, v_conc, v_form))

        LOGGER.info("Quantitativo de exemplo CHRONOS FUNDAÇÃO populado com sucesso (15 lançamentos).")

