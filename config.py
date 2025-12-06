from pathlib import Path

# Directory that holds this config file
BASE_DIR = Path(__file__).resolve().parent

# Application folders
CACHE_DIR = BASE_DIR / "cache"
PDF_DIR = BASE_DIR / "pdfs"
LOG_DIR = BASE_DIR / "logs"

# App settings
ENABLE_LOGGING = True

# Ensure folders exist
for folder in (CACHE_DIR, PDF_DIR, LOG_DIR):
    folder.mkdir(parents=True, exist_ok=True)

LOG_FILE = BASE_DIR / "cron_log.txt"