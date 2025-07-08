#!/bin/bash

echo "Building radarr-extractor with LinuxServer.io PUID/PGID support"

# Build the Docker image (PUID/PGID handled at runtime via environment variables)
docker build --platform linux/amd64 -t crzyc/radarr-extractor:latest .

echo "Build completed successfully!"
echo "PUID/PGID are configured at runtime via environment variables:"
echo "  docker run -e PUID=1000 -e PGID=1000 crzyc/radarr-extractor:latest"
echo ""
echo "To push to Docker Hub, run:"
echo "  docker login"
echo "  docker push crzyc/radarr-extractor:latest"

# Optionally push (uncomment if you want automatic push)
# docker login
# docker push crzyc/radarr-extractor:latest