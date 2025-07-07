#!/bin/bash

# Set default values for PUID and PGID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Starting radarr-extractor with PUID=$PUID and PGID=$PGID"

# Get current user info
CURRENT_UID=$(id -u appuser)
CURRENT_GID=$(id -g appuser)

# Check if we need to modify the user
if [ "$PUID" != "$CURRENT_UID" ] || [ "$PGID" != "$CURRENT_GID" ]; then
    echo "Updating appuser UID from $CURRENT_UID to $PUID and GID from $CURRENT_GID to $PGID"
    
    # Modify the group first
    groupmod -o -g "$PGID" appuser
    
    # Modify the user
    usermod -o -u "$PUID" appuser
    
    # Update ownership of application directory
    chown -R appuser:appuser /app
    
    # Update ownership of downloads directory if it exists
    if [ -d "/downloads" ]; then
        chown -R appuser:appuser /downloads
    fi
    
    echo "User permissions updated successfully"
else
    echo "User already has correct UID/GID, no changes needed"
fi

# Switch to the appuser and execute the main command
echo "Starting application as appuser (UID=$PUID, GID=$PGID)"
exec gosu appuser "$@"