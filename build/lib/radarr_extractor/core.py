import os
import logging
import rarfile
import requests
from watchdog.events import FileSystemEventHandler
from radarr_extractor.config import RADARR_API_KEY, RADARR_URL, EXTRACTED_DIR, logger

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
            logger.info("Using rarfile for extraction")
            with rarfile.RarFile(archive_path) as rf:
                rf.extractall(extract_dir)
        
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
        logger.info(f"Found compressed file, starting extraction: {file_path}")
        
        try:
            logger.info(f"Starting extraction of: {file_path}")
            extracted_path = extract_archive(file_path)
            logger.info(f"Successfully extracted to: {extracted_path}")
            notify_radarr(extracted_path)
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}")
    else:
        logger.info(f"File is not compressed, skipping: {file_path}")

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

class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"File system event - New file detected: {event.src_path}")
            process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            logger.info(f"File system event - File modified: {event.src_path}")
