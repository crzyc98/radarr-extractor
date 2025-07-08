#!/bin/bash
set -e

# Set defaults
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "=========================================="
echo "PUID/PGID Configuration"
echo "=========================================="
echo "Starting radarr-extractor with PUID=$PUID and PGID=$PGID"

# Validate inputs
if ! [[ "$PUID" =~ ^[0-9]+$ ]] || [ "$PUID" -eq 0 ]; then
    echo "WARNING: Invalid PUID=$PUID, using default 1000"
    PUID=1000
fi

if ! [[ "$PGID" =~ ^[0-9]+$ ]] || [ "$PGID" -eq 0 ]; then
    echo "WARNING: Invalid PGID=$PGID, using default 1000"
    PGID=1000
fi

echo "Validated PUID: $PUID, PGID: $PGID"

# Create group if it doesn't exist
if ! getent group abc >/dev/null 2>&1; then
    echo "Creating group abc with GID $PGID"
    groupadd -g "$PGID" abc
else
    echo "Group abc already exists"
    # Update GID if different
    CURRENT_GID=$(getent group abc | cut -d: -f3)
    if [ "$CURRENT_GID" != "$PGID" ]; then
        echo "Updating group abc GID from $CURRENT_GID to $PGID"
        groupmod -g "$PGID" abc
    fi
fi

# Create user if it doesn't exist
if ! getent passwd abc >/dev/null 2>&1; then
    echo "Creating user abc with UID $PUID"
    useradd -u "$PUID" -g "$PGID" -d /config -s /bin/bash abc
else
    echo "User abc already exists"
    # Update UID if different
    CURRENT_UID=$(getent passwd abc | cut -d: -f3)
    if [ "$CURRENT_UID" != "$PUID" ]; then
        echo "Updating user abc UID from $CURRENT_UID to $PUID"
        usermod -u "$PUID" -g "$PGID" abc
    fi
fi

# Set up directories with proper ownership
echo "Setting up directories..."
mkdir -p /config /downloads /downloads/.extracted_files

echo "Setting ownership of directories to abc:abc"
chown -R abc:abc /app /config /downloads

# Verify setup
echo "Directory ownership verification:"
echo "  /app: $(ls -ld /app | awk '{print $3":"$4}')"
echo "  /config: $(ls -ld /config | awk '{print $3":"$4}')"
echo "  /downloads: $(ls -ld /downloads | awk '{print $3":"$4}')"

echo "User verification:"
echo "  abc user: $(id abc)"

echo "Troubleshooting commands:"
echo "  Host: Run 'id \$USER' to find your UID/GID"
echo "  Container: Run 'docker exec <container> id abc'"
echo "=========================================="

# Start application as abc user
echo "Starting application as abc (UID:$PUID, GID:$PGID)"
exec /usr/local/bin/gosu abc "$@"