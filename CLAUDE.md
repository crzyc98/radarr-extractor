# Radarr Extractor - Development Guide

## Project Overview
Python Flask application that automatically extracts compressed movie files and notifies Radarr to rescan the extracted content.

## Development Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application
```bash
# Activate virtual environment
source venv/bin/activate

# Run the main application
python -m radarr_extractor.main
```

## Testing
```bash
# Run tests
python -m pytest tests/
```

## Dependencies
- Flask - Web framework for webhook handling
- requests - HTTP client for Radarr API calls
- rarfile - RAR archive extraction
- watchdog - File system monitoring

## Key Components
- `radarr_extractor/main.py` - Flask app entry point
- `radarr_extractor/core.py` - Core extraction logic
- `radarr_extractor/config.py` - Configuration management
- `radarr_extractor/tracker.py` - File monitoring
- `radarr_extractor/utils.py` - Utility functions

## Environment Variables
- `RADARR_URL` - Radarr instance URL
- `RADARR_API_KEY` - Radarr API key
- `DOWNLOAD_DIR` - Download directory path

## Docker Support
```bash
# Build Docker image
./docker-build.sh

# Run with docker-compose
docker-compose up -d
```