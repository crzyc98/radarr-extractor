#!/usr/bin/env sh
set -e

# Default PUID/PGID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "=== ENTRYPOINT DEBUG ==="
echo "Starting radarr-extractor with PUID=$PUID, PGID=$PGID"
echo "Current user: $(whoami)"
echo "Current UID: $(id -u)"
echo "Current GID: $(id -g)"
echo "Arguments: $@"

# Ensure directories exist and have correct ownership
echo "Creating directories..."
mkdir -p /downloads /downloads/extracted /config 2>/dev/null || true

# Only try to change ownership if we have permission
echo "Setting ownership..."
if [ "$(id -u)" = "0" ]; then
    chown -R "${PUID}:${PGID}" /app /downloads /config 2>/dev/null || true
    echo "Ownership set (running as root)"
else
    echo "Not running as root, skipping ownership change"
fi

# Create the tracker file with proper permissions (remove if it's a directory)
rm -rf /downloads/.extracted_files 2>/dev/null || true
touch /downloads/.extracted_files 2>/dev/null || true
if [ "$(id -u)" = "0" ]; then
    chown "${PUID}:${PGID}" /downloads/.extracted_files 2>/dev/null || true
fi
echo "Tracker file created"

# Show directory permissions
echo "Directory permissions:"
ls -la /downloads/
ls -la /app/

# Try to drop to the unprivileged user, fall back to root if not permitted
if gosu "${PUID}:${PGID}" true 2>/dev/null; then
    echo "Dropping to user ${PUID}:${PGID}"
    echo "About to execute: gosu ${PUID}:${PGID} $@"
    exec gosu "${PUID}:${PGID}" "$@"
else
    echo "Warning: Cannot switch to user ${PUID}:${PGID}, running as root"
    echo "About to execute as root: $@"
    exec "$@"
fi
