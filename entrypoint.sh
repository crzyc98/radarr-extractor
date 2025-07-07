#!/bin/bash
set -e

# Set default values for PUID and PGID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Starting radarr-extractor with PUID=$PUID and PGID=$PGID"

# Get current user info
CURRENT_UID=$(id -u appuser 2>/dev/null || echo "1000")
CURRENT_GID=$(id -g appuser 2>/dev/null || echo "1000")

echo "Current appuser UID: $CURRENT_UID, GID: $CURRENT_GID"
echo "Requested PUID: $PUID, PGID: $PGID"

# Check if we need to modify the user
if [ "$PUID" != "$CURRENT_UID" ] || [ "$PGID" != "$CURRENT_GID" ]; then
    echo "Updating appuser UID from $CURRENT_UID to $PUID and GID from $CURRENT_GID to $PGID"
    
    # Modify the group first
    groupmod -o -g "$PGID" appuser
    
    # Modify the user
    usermod -o -u "$PUID" appuser
    
    echo "User permissions updated successfully"
else
    echo "User already has correct UID/GID, no changes needed"
fi

# Update ownership of application directory
echo "Setting ownership of /app to appuser:appuser"
chown -R appuser:appuser /app

# Update ownership of downloads directory if it exists
if [ -d "/downloads" ]; then
    echo "Setting ownership of /downloads to appuser:appuser"
    chown -R appuser:appuser /downloads
fi

# Create extracted_files directory with proper permissions
if [ -d "/downloads" ]; then
    echo "Creating /downloads/.extracted_files directory"
    mkdir -p /downloads/.extracted_files
    chown appuser:appuser /downloads/.extracted_files
fi

# Switch to the appuser and execute the main command
echo "Starting application as appuser (UID=$PUID, GID=$PGID)"
exec /usr/local/bin/gosu appuser "$@"