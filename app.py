"""Bootstrap e Ponto de Entrada do Sistema de Gestão de Obras & Tarefas.
Padrão Sênior: Separação de responsabilidades, migrações automáticas e tratamento robusto.
"""

import sys
import customtkinter as ctk
import json
from config import LOGGER, APP_TITLE, APP_VERSION, PREFS_PATH
from database.migrator import init_database, migrate_legacy_data_if_needed, seed_sample_quantitativos_if_needed
from ui.main_window import MainWindow

def bootstrap():
    """Inicializa camadas de infraestrutura, banco de dados e interface gráfica."""
    LOGGER.info("Iniciando %s v%s...", APP_TITLE, APP_VERSION)

    # 1. Configurações Globais do CustomTkinter
    saved_theme = "System"
    try:
        if PREFS_PATH.exists():
            prefs = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
            saved_theme = prefs.get("theme", "System")
    except Exception:
        pass
    ctk.set_appearance_mode(saved_theme)
    ctk.set_default_color_theme("blue")

    # 2. Inicialização do Banco de Dados SQLite e Auto-Migração
    try:
        init_database()
        migrated = migrate_legacy_data_if_needed()
        seed_sample_quantitativos_if_needed()
        if migrated > 0:
            LOGGER.info("Migração automática concluída com sucesso (%d tarefas importadas).", migrated)
    except Exception as e:
        LOGGER.critical("Falha fatal na inicialização do banco de dados: %s", e, exc_info=True)
        sys.exit(1)

    # 3. Inicialização da Interface Gráfica
    try:
        app = MainWindow()
        LOGGER.info("Interface gráfica inicializada. Iniciando loop de eventos.")
        app.mainloop()
    except Exception as e:
        LOGGER.critical("Erro inesperado durante a execução do aplicativo: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    bootstrap()
