import os
import sys
import threading
from urllib.parse import quote
from flask import Flask, request, jsonify, render_template, redirect, url_for
from watchdog.observers import Observer
from radarr_extractor.config import DOWNLOAD_DIR, WEBHOOK_PORT, logger
from radarr_extractor.core import scan_directory, DownloadHandler, process_file, is_compressed_file
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

# ---- Simple LAN-only UI for manual extraction ----
def _resolve_safe_path(user_path: str) -> str:
    """Resolve a user-supplied path safely inside DOWNLOAD_DIR.
    Accepts absolute paths under DOWNLOAD_DIR or paths relative to it.
    Raises ValueError for traversal or out-of-root paths.
    """
    if not user_path:
        return DOWNLOAD_DIR
    # If relative, join to DOWNLOAD_DIR; if absolute, keep but validate
    candidate = user_path
    if not os.path.isabs(candidate):
        candidate = os.path.join(DOWNLOAD_DIR, candidate)
    candidate = os.path.realpath(candidate)
    root = os.path.realpath(DOWNLOAD_DIR)
    if os.path.commonpath([root, candidate]) != root:
        raise ValueError("Path outside monitored directory")
    return candidate

def _breadcrumbs(abs_path: str):
    root = os.path.realpath(DOWNLOAD_DIR)
    parts = []
    # Build breadcrumb segments from root to current
    rel = os.path.relpath(abs_path, root)
    if rel == '.' or rel.startswith('..'):
        return [("/browse", "/")]  # root only
    accum = ""
    parts.append((url_for('browse'), "/"))
    for segment in rel.split(os.sep):
        accum = os.path.join(accum, segment)
        parts.append((url_for('browse', path=accum), segment))
    return parts

@app.route('/browse', methods=['GET'])
def browse():
    # Default to DOWNLOAD_DIR
    user_path = request.args.get('path', '')
    message = request.args.get('msg')
    try:
        abs_path = _resolve_safe_path(user_path)
    except ValueError as e:
        logger.warning(f"Rejected browse path '{user_path}': {e}")
        return jsonify({"error": "Invalid path"}), 400

    if not os.path.exists(abs_path):
        return jsonify({"error": "Path not found"}), 404

    entries = []
    try:
        with os.scandir(abs_path) as it:
            for entry in it:
                # Hide some noisy files
                if entry.name in {'.', '..', '.DS_Store', '.extracted_files'}:
                    continue
                epath = os.path.join(abs_path, entry.name)
                item = {
                    'name': entry.name,
                    'is_dir': entry.is_dir(),
                    'path': epath,
                    'rel': os.path.relpath(epath, DOWNLOAD_DIR),
                    'is_archive': False
                }
                if entry.is_file():
                    item['is_archive'] = is_compressed_file(entry.name)
                entries.append(item)
    except PermissionError:
        return jsonify({"error": "Permission denied"}), 403

    # Sort: directories first, then files alphabetically
    entries.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

    crumbs = _breadcrumbs(abs_path)
    at_root = os.path.realpath(abs_path) == os.path.realpath(DOWNLOAD_DIR)
    parent_rel = None if at_root else os.path.relpath(os.path.dirname(abs_path), DOWNLOAD_DIR)

    return render_template(
        'browse.html',
        current_path=abs_path,
        entries=entries,
        breadcrumbs=crumbs,
        at_root=at_root,
        parent_rel=parent_rel,
        message=message,
    )

@app.route('/extract', methods=['POST'])
def extract_route():
    target = request.form.get('path', '')
    try:
        abs_target = _resolve_safe_path(target)
    except ValueError as e:
        logger.warning(f"Rejected extract path '{target}': {e}")
        return jsonify({"error": "Invalid path"}), 400

    if not os.path.isfile(abs_target) or not is_compressed_file(abs_target):
        return jsonify({"error": "Not an archive file"}), 400

    def _bg():
        logger.info(f"UI-triggered extraction for: {abs_target}")
        process_file(abs_target)

    threading.Thread(target=_bg, daemon=True).start()
    current_dir = os.path.dirname(abs_target)
    rel = os.path.relpath(current_dir, DOWNLOAD_DIR)
    return redirect(url_for('browse', path=rel, msg=f"Extraction queued for {os.path.basename(abs_target)}"))

@app.route('/rescan', methods=['POST'])
def rescan_route():
    target = request.form.get('path', '')
    try:
        abs_target = _resolve_safe_path(target)
    except ValueError as e:
        logger.warning(f"Rejected rescan path '{target}': {e}")
        return jsonify({"error": "Invalid path"}), 400

    if not os.path.isdir(abs_target):
        return jsonify({"error": "Not a directory"}), 400

    def _bg():
        logger.info(f"UI-triggered rescan for: {abs_target}")
        scan_directory(abs_target)

    threading.Thread(target=_bg, daemon=True).start()
    rel = os.path.relpath(abs_target, DOWNLOAD_DIR)
    return redirect(url_for('browse', path=rel, msg=f"Rescan started"))

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
        # Start the file system observer first
        logger.info("Starting file system observer...")
        event_handler = DownloadHandler()
        observer = Observer()
        observer.schedule(event_handler, DOWNLOAD_DIR, recursive=True)
        observer.start()
        logger.info("File system observer started with recursive monitoring")

        # Start the Flask webhook server
        logger.info(f"Starting webhook server on port {WEBHOOK_PORT}")
        logger.info("Flask app is about to start...")
        
        # Start directory scan in a separate thread so it doesn't block Flask startup
        def background_scan():
            logger.info("Starting background directory scan...")
            scan_directory(DOWNLOAD_DIR)
            logger.info("Background directory scan completed")
        
        scan_thread = threading.Thread(target=background_scan, daemon=True)
        scan_thread.start()
        
        # Start Flask server (this will block)
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
