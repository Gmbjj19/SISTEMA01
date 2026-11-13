import sqlite3
from contextlib import contextmanager
from typing import Generator
from pathlib import Path
from config import DATABASE_PATH, LOGGER

class DatabaseManager:
    """Gerenciador centralizado de conexões SQLite com suporte a WAL e RowFactory."""
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            # Ativa WAL (Write-Ahead Logging) para alta concorrência e desempenho
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            LOGGER.error("Erro durante transação no banco de dados: %s", e)
            raise
        finally:
            conn.close()

db_manager = DatabaseManager()

