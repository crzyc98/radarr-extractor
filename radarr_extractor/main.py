import os
import sys
from flask import Flask, request, jsonify
from watchdog.observers import Observer
from radarr_extractor.config import DOWNLOAD_DIR, WEBHOOK_PORT, logger
from radarr_extractor.core import scan_directory, DownloadHandler, process_file
app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'radarr-extractor',
        'monitored_directory': DOWNLOAD_DIR
    }), 200

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
            
            if os.path.exists(file_path):
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

def main():
    print("=== MAIN.PY DEBUG START ===")
    print(f"Python path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Current user: {os.getuid()}:{os.getgid()}")
    
    logger.info("Starting Radarr Download Extractor")
    logger.info(f"Monitoring directory: {DOWNLOAD_DIR}")
    logger.info(f"Webhook port: {WEBHOOK_PORT}")
    
    # Check if download directory exists and is accessible
    if not os.path.exists(DOWNLOAD_DIR):
        logger.error(f"Download directory does not exist: {DOWNLOAD_DIR}")
        return
    
    if not os.access(DOWNLOAD_DIR, os.R_OK | os.W_OK):
        logger.error(f"No read/write access to download directory: {DOWNLOAD_DIR}")
        return
    
    logger.info("Download directory is accessible")
    
    # Check if we can create the tracker file
    from radarr_extractor.config import TRACKER_FILE
    try:
        with open(TRACKER_FILE, 'a') as f:
            pass  # Just test if we can open it
        logger.info("Tracker file is accessible")
    except Exception as e:
        logger.error(f"Cannot access tracker file {TRACKER_FILE}: {e}")
        return
    
    try:
        # Recursively scan download directory for existing files
        logger.info("Starting directory scan...")
        scan_directory(DOWNLOAD_DIR)
        logger.info("Directory scan completed")
        
        # Start the file system observer
        logger.info("Starting file system observer...")
        event_handler = DownloadHandler()
        observer = Observer()
        observer.schedule(event_handler, DOWNLOAD_DIR, recursive=True)
        observer.start()
        logger.info("File system observer started with recursive monitoring")

        # Start the Flask webhook server
        logger.info(f"Starting webhook server on port {WEBHOOK_PORT}")
        logger.info("Flask app is about to start...")
        app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False)
        
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()