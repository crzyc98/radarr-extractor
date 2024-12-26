import os
from radarr_extractor.config import TRACKER_FILE, logger

def load_extracted_files():
    """Load the list of extracted files from the tracker file."""
    extracted_files = set()
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            for line in f:
                extracted_files.add(line.strip())
    return extracted_files

def record_extracted_file(file_path):
    """Record a successfully extracted file."""
    logger.info(f"Recording extracted file: {file_path}")
    with open(TRACKER_FILE, 'a') as f:
        f.write(file_path + '\n')

def is_file_extracted(file_path):
    """Check if a file has already been extracted."""
    extracted_files = load_extracted_files()
    return file_path in extracted_files