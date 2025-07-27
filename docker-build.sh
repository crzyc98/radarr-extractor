#!/bin/bash

# Default PUID/PGID values for build-time user creation
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Building radarr-extractor with appuser fix (PUID=$PUID, PGID=$PGID)"

# Build the Docker image with build args to create appuser
docker build \
    --platform linux/amd64 \
    --build-arg PUID=$PUID \
    --build-arg PGID=$PGID \
    -t crzyc/radarr-extractor:latest .

echo "Build completed successfully!"
echo "Built with appuser created as UID:$PUID, GID:$PGID"
echo ""
echo "To push to Docker Hub, run:"
echo "  docker login"
echo "  docker push crzyc/radarr-extractor:latest"

# Optionally push (uncomment if you want automatic push)
# docker login
# docker push crzyc/radarr-extractor:latest