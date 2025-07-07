# Radarr Extractor

A Python Flask application that automatically extracts compressed movie files and notifies Radarr to rescan the extracted content.

## Features

- **Automatic extraction**: Supports RAR, ZIP, 7Z, TAR.GZ, and TAR.BZ2 archives
- **Directory monitoring**: Watches download directory for new files
- **Radarr integration**: Automatically notifies Radarr via API to rescan extracted files
- **Webhook support**: Receives notifications from Radarr when downloads complete
- **Docker support**: Easy deployment with Docker and Docker Compose

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/crzyc98/radarr-extractor.git
cd radarr-extractor
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker

A Docker image is available: `crzyc98/radarr-extractor:latest`

```bash
docker run -d -p 9898:9898 \
    -e RADARR_URL=http://your-radarr-instance:7878 \
    -e RADARR_API_KEY=your-api-key-here \
    -e DOWNLOAD_DIR=/downloads \
    -v /path/to/your/downloads:/downloads \
    crzyc98/radarr-extractor:latest
```

Or use Docker Compose:
```bash
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `RADARR_URL` | URL of your Radarr instance | `http://localhost:7878` |
| `RADARR_API_KEY` | Your Radarr API key | `abcd1234efgh5678ijkl` |
| `DOWNLOAD_DIR` | Directory where downloads are stored | `/downloads` |

### Radarr Webhook Setup

1. In Radarr, go to **Settings** → **Connect**
2. Add a new **Webhook** connection
3. Set the URL to: `http://your-extractor-host:9898/webhook`
4. Enable **On Download** and **On Upgrade** triggers

## Usage

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export RADARR_URL=http://localhost:7878
export RADARR_API_KEY=your-api-key
export DOWNLOAD_DIR=/path/to/downloads

# Run the application
python -m radarr_extractor.main
```

### Running Tests
```bash
python -m pytest tests/
```

## Supported Archive Formats

- RAR (`.rar`)
- ZIP (`.zip`)
- 7-Zip (`.7z`)
- TAR.GZ (`.tar.gz`)
- TAR.BZ2 (`.tar.bz2`)

## Troubleshooting

### Common Issues

**Application not receiving webhooks:**
- Verify the webhook URL is correctly set in Radarr
- Check that port 9898 is accessible from Radarr
- Review application logs for any errors

**Extraction failures:**
- Ensure the download directory has proper read/write permissions
- Check that required extraction tools are installed (especially for RAR files)
- Verify archive files are not corrupted

**Radarr not rescanning:**
- Confirm `RADARR_URL` and `RADARR_API_KEY` are correct
- Check Radarr logs for API call errors
- Verify the extracted files are in the correct location

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Dependencies

- **Flask**: Web framework for webhook handling
- **requests**: HTTP client for Radarr API calls
- **rarfile**: RAR archive extraction support
- **watchdog**: File system monitoring