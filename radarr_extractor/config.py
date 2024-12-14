import os
import logging

# Configuration
RADARR_URL = os.environ.get('RADARR_URL')
RADARR_API_KEY = os.environ.get('RADARR_API_KEY')
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/downloads')
EXTRACTED_DIR = os.path.join(DOWNLOAD_DIR, 'extracted')
WEBHOOK_PORT = int(os.environ.get('WEBHOOK_PORT', '9898'))

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ensure extracted directory exists
os.makedirs(EXTRACTED_DIR, exist_ok=True)
