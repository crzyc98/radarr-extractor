#!/bin/bash
set -e

# Set default values for PUID and PGID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Starting radarr-extractor with PUID=$PUID and PGID=$PGID"

# Check if we're running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Container must be run as root to modify user permissions"
    echo "Current user: $(id -u):$(id -g)"
    exit 1
fi

# Get current user info
CURRENT_UID=$(id -u appuser 2>/dev/null || echo "1000")
CURRENT_GID=$(id -g appuser 2>/dev/null || echo "1000")

echo "Current appuser UID: $CURRENT_UID, GID: $CURRENT_GID"
echo "Requested PUID: $PUID, PGID: $PGID"

# Check if we need to modify the user
if [ "$PUID" != "$CURRENT_UID" ] || [ "$PGID" != "$CURRENT_GID" ]; then
    echo "Updating appuser UID from $CURRENT_UID to $PUID and GID from $CURRENT_GID to $PGID"
    
    # Kill any processes that might be using the user/group files
    pkill -f "appuser" 2>/dev/null || true
    
    # Wait a moment for processes to exit
    sleep 1
    
    # Modify the group first
    if ! groupmod -o -g "$PGID" appuser 2>/dev/null; then
        echo "Warning: Could not modify group, trying to delete and recreate..."
        # Try to delete and recreate the group
        groupdel appuser 2>/dev/null || true
        groupadd -g "$PGID" appuser
    fi
    
    # Modify the user
    if ! usermod -o -u "$PUID" -g "$PGID" appuser 2>/dev/null; then
        echo "Warning: Could not modify user, trying to delete and recreate..."
        # Try to delete and recreate the user
        userdel appuser 2>/dev/null || true
        useradd -u "$PUID" -g "$PGID" -M -s /bin/bash appuser
    fi
    
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