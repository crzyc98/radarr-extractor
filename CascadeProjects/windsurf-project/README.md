# Radarr Download Extractor

## Overview
This Python script monitors a download folder for compressed files (RAR, ZIP, 7z, etc.) and automatically extracts them. It integrates with Radarr in two ways:
1. Listens for Radarr webhook notifications about new downloads
2. Actively monitors the download directory as a fallback

## Features
- Responds to Radarr download webhooks
- Monitors download directory for compressed archives
- Supports multiple archive formats (RAR, ZIP, 7z, etc.)
- Automatically extracts archives
- Notifies Radarr to rescan extracted files

## Prerequisites
- Docker
- Radarr instance
- Download folder accessible to the container

## Environment Variables
- `RADARR_URL`: URL of your Radarr instance (default: `http://192.168.99.30:7878`)
- `RADARR_API_KEY`: Your Radarr API key
- `DOWNLOAD_DIR`: Path to the download folder (default: `/downloads`)
- `WEBHOOK_PORT`: Port for the webhook server (default: `9898`)

## Docker Deployment
```bash
docker run -d \
  -e RADARR_URL=http://192.168.99.30:7878 \
  -e RADARR_API_KEY=8b196869cab34899b741e7340423ed18 \
  -p 9898:9898 \
  -v /mnt/Pool1/bigdata/download/completed:/downloads \
  radarr-extractor
```

## Building the Docker Image
```bash
docker build -t radarr-extractor .
```

## Radarr Configuration
1. Go to Settings > Connect in Radarr
2. Add a new Webhook connection
3. Set the URL to `http://your-host:9898/webhook`
4. Enable "On Download" notification

## Configuring Radarr Webhook

1. Go to Settings > Connect in Radarr
2. Add a new Webhook connection
3. Set the URL to `http://your-host:9898/webhook`
4. Enable the following notifications:
   - "On File Import" (triggered when Radarr imports a completed download)
   - "On File Upgrade" (triggered when Radarr upgrades a movie to better quality)
5. Optionally enable other notifications as needed

## Verifying Deployment

1. Check the service health by accessing the health endpoint:
   ```
   curl http://<your-host-ip>:9898/
   ```
   You should receive a response like:
   ```json
   {
     "monitored_directory": "/downloads",
     "service": "radarr-extractor",
     "status": "healthy"
   }
   ```

2. Configure Radarr webhook:
   - In Radarr, go to Settings > Connect > Add Connection > Webhook
   - Set the URL to: `http://<your-host-ip>:9898/webhook`
   - Enable notifications for "On Import" and "On Download"

3. Monitor the logs to verify webhook notifications:
   ```
   docker logs radarr-extractor
   ```

## Troubleshooting
- Ensure Radarr API key is correct
- Check container logs for extraction and notification errors
- Verify mount points and permissions
- Confirm webhook port is accessible from Radarr

## Security Notes
- Never share your Radarr API key publicly
- Use environment variables for sensitive information
- Consider network security when exposing the webhook port
