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

