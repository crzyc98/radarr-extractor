import os
import logging

# Basic configuration values (no side effects on import)
RADARR_URL = os.environ.get('RADARR_URL')
RADARR_API_KEY = os.environ.get('RADARR_API_KEY')
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/downloads')
EXTRACTED_DIR = os.path.join(DOWNLOAD_DIR, 'extracted')
WEBHOOK_PORT = int(os.environ.get('WEBHOOK_PORT', '9898'))

# Extraction mode: 'inplace' (default) or 'extracted_dir'
EXTRACT_MODE = os.environ.get('EXTRACT_MODE', 'inplace').strip().lower()

# Whether to notify Radarr after extraction (default: true)
def _parse_bool(val: str, default: bool) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}

RADARR_NOTIFY = _parse_bool(os.environ.get('RADARR_NOTIFY'), True)

# Performance and selection
MAX_CONCURRENT_EXTRACTS = int(os.environ.get('MAX_CONCURRENT_EXTRACTS', '1'))
EXTRACT_ONLY_MEDIA = _parse_bool(os.environ.get('EXTRACT_ONLY_MEDIA'), False)

# Stability tuning
STABILITY_WINDOW_SEC = int(os.environ.get('STABILITY_WINDOW_SEC', '10'))
STABILITY_POLLS = int(os.environ.get('STABILITY_POLLS', '3'))
MAX_WAIT_PER_ARCHIVE_SEC = int(os.environ.get('MAX_WAIT_PER_ARCHIVE_SEC', '300'))

# Backend selection (placeholder): 'python' or 'system_fast'
EXTRACT_BACKEND = os.environ.get('EXTRACT_BACKEND', 'python').strip().lower()

# Tracker file
TRACKER_FILE = os.path.join(DOWNLOAD_DIR, '.extracted_files')

# Logger (configured in main at runtime)
logger = logging.getLogger('radarr_extractor')
