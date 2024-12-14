import os
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