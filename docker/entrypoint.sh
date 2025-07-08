#!/usr/bin/env sh
set -eu

# Default PUID/PGID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Starting radarr-extractor with PUID=$PUID, PGID=$PGID"

# Ensure directories exist and have correct ownership
mkdir -p /downloads /downloads/extracted /downloads/.extracted_files /config
chown -R "${PUID}:${PGID}" /app /downloads /config || true

# Drop to the unprivileged user and execute the command
exec gosu "${PUID}:${PGID}" "$@"