import os
import sys
import logging
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "gestao_obras.db"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
LOGO_DARK_PATH = ASSETS_DIR / "logo_dark.png"
LOGO_LIGHT_PATH = ASSETS_DIR / "logo_light.png"
LOGO_PDF_PATH = ASSETS_DIR / "logo_pdf.png"
APP_ICON_PATH = ASSETS_DIR / "icon.ico"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "app.log"

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

LOGGER = logging.getLogger("GestaoObras")

# Configurações da Aplicação
APP_TITLE = "MARCON EMPREITEIRA • Gestão de Obras & Engenharia"
APP_VERSION = "2.0.0-PRO"
WINDOW_DEFAULT_SIZE = "1180x760"
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 620

# Arquivos Legados para Auto-Migração
LEGACY_FILES = [
    BASE_DIR / "tasks_enterprise.json",
    BASE_DIR / "tasks_ultimate.json",
    BASE_DIR / "tasks_pro.json",
    BASE_DIR / "tasks.json"
]

