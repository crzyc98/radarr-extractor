# Radarr Extractor

This is a simple Python application that extracts downloaded files and notifies Radarr.

## Features

- Monitors a specified download directory for new files.
- Extracts compressed archives (rar, zip, 7z, tar.gz, tar.bz2).
- Notifies Radarr to rescan the extracted files.

## Configuration

The following environment variables are required:

- `RADARR_URL`: The URL of your Radarr instance.
- `RADARR_API_KEY`: Your Radarr API key.
- `DOWNLOAD_DIR`: The directory where your downloads are stored.

## Usage

1. Set the required environment variables.
2. Run the application using `python -m radarr_extractor.main`.
3. Radarr will send webhook notifications to the application when a download is complete.

## Dependencies

- requests
- flask
- rarfile
- watchdog