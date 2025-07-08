#!/bin/bash

# Default PUID/PGID values
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Building radarr-extractor with PUID=$PUID and PGID=$PGID"

# Build the Docker image with build args
docker build \
    --platform linux/amd64 \
    --build-arg PUID=$PUID \
    --build-arg PGID=$PGID \
    -t crzyc/radarr-extractor:latest .

echo "Build completed successfully!"
echo "To push to Docker Hub, run:"
echo "  docker login"
echo "  docker push crzyc/radarr-extractor:latest"

# Optionally push (uncomment if you want automatic push)
# docker login
# docker push crzyc/radarr-extractor:latest