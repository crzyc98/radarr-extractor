import os
import time
import logging
import rarfile
import requests
import patoolib
from flask import Flask, request, jsonify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
RADARR_URL = os.environ.get('RADARR_URL', 'http://192.168.99.30:7878')
RADARR_API_KEY = os.environ.get('RADARR_API_KEY', '8b196869cab34899b741e7340423ed18')
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

# Initialize Flask app for webhook
app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'radarr-extractor',
        'monitored_directory': DOWNLOAD_DIR
    }), 200

def is_compressed_file(filename):
    """Check if file is a compressed archive."""
    compressed_extensions = ['.rar', '.zip', '.7z', '.tar.gz', '.tar.bz2']
    return any(filename.lower().endswith(ext) for ext in compressed_extensions)

def extract_archive(archive_path):
    """Extract archive to the extracted directory."""
    logger.info(f"Starting archive extraction for: {archive_path}")
    
    # Create unique extraction directory
    extract_dir = os.path.join(EXTRACTED_DIR, os.path.basename(archive_path) + '_extracted')
    os.makedirs(extract_dir, exist_ok=True)
    logger.info(f"Created extraction directory: {extract_dir}")

    try:
        if archive_path.lower().endswith('.rar'):
            logger.info("Detected RAR archive, using unrar")
            with rarfile.RarFile(archive_path) as rf:
                rf.extractall(extract_dir)
        else:
            logger.info("Using patool for extraction")
            patoolib.extract_archive(archive_path, outdir=extract_dir)
        
        logger.info(f"Extraction completed successfully to: {extract_dir}")
        return extract_dir
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise

def notify_radarr(extracted_path):
    """Notify Radarr about the new extracted files."""
    try:
        headers = {
            'X-Api-Key': RADARR_API_KEY,
            'Content-Type': 'application/json'
        }
        
        endpoint = f"{RADARR_URL}/api/v3/command"
        payload = {
            "name": "RescanMovie",
            "path": extracted_path
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Notified Radarr to rescan: {extracted_path}")
    except Exception as e:
        logger.error(f"Failed to notify Radarr: {e}")

def process_file(file_path):
    """Process a downloaded file if it's compressed."""
    logger.info(f"Checking file for extraction: {file_path}")
    if is_compressed_file(file_path):
        # Wait a moment to ensure file is fully written
        logger.info(f"Found compressed file, waiting 5 seconds before extraction: {file_path}")
        time.sleep(5)
        
        try:
            logger.info(f"Starting extraction of: {file_path}")
            extracted_path = extract_archive(file_path)
            logger.info(f"Successfully extracted to: {extracted_path}")
            notify_radarr(extracted_path)
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}")
            logger.exception("Full error details:")
    else:
        logger.info(f"File is not compressed, skipping: {file_path}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Radarr webhook notifications."""
    data = request.get_json()
    
    # Log the event type for debugging
    event_type = data.get('eventType')
    logger.info(f"Received webhook event: {event_type}")
    
    # Handle Download, MovieFileImported, and MovieFileUpgraded events
    if event_type in ['Download', 'MovieFileImported', 'MovieFileUpgraded']:
        movie_file = data.get('movieFile', {}).get('relativePath')
        movie_title = data.get('movie', {}).get('title', 'Unknown Movie')
        
        if movie_file:
            file_path = os.path.join(DOWNLOAD_DIR, movie_file)
            logger.info(f"Processing {event_type} for movie '{movie_title}': {file_path}")
            
            if os.path.exists(file_path) and is_compressed_file(file_path):
                process_file(file_path)
                return jsonify({
                    'status': 'processing',
                    'file': file_path,
                    'movie': movie_title,
                    'event': event_type
                }), 200
            else:
                logger.info(f"File either doesn't exist or is not compressed: {file_path}")
    
    return jsonify({'status': 'ignored', 'event': event_type}), 200

class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"File system event - New file detected: {event.src_path}")
            process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            logger.info(f"File system event - File modified: {event.src_path}")

def scan_directory(directory):
    """Recursively scan directory for compressed files."""
    logger.info(f"Scanning directory: {directory}")
    try:
        for root, dirs, files in os.walk(directory):
            logger.info(f"Checking subfolder: {root}")
            for file in files:
                full_path = os.path.join(root, file)
                logger.info(f"Found file: {full_path}")
                if is_compressed_file(full_path):
                    logger.info(f"Found compressed file: {full_path}")
                    process_file(full_path)
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")

def main():
    logger.info("Starting Radarr Download Extractor")
    logger.info(f"Monitoring directory: {DOWNLOAD_DIR}")
    
    # Recursively scan download directory for existing files
    scan_directory(DOWNLOAD_DIR)
    
    # Start the file system observer
    event_handler = DownloadHandler()
    observer = Observer()
    observer.schedule(event_handler, DOWNLOAD_DIR, recursive=True)
    observer.start()
    logger.info("File system observer started with recursive monitoring")

    try:
        # Start the Flask webhook server
        logger.info(f"Starting webhook server on port {WEBHOOK_PORT}")
        app.run(host='0.0.0.0', port=WEBHOOK_PORT)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()
