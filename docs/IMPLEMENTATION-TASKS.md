# Implementation Tasks - PUID/PGID Fix

## Immediate Action Items

Based on the epic and stories analysis, here are the concrete tasks to fix the current PUID/PGID implementation:

### Task 1: Replace Entrypoint Script with LinuxServer.io Pattern
**Priority**: CRITICAL  
**Estimated Time**: 2 hours  

#### Current Problem
The existing entrypoint script tries to modify the existing `appuser` which fails due to permission issues.

#### Solution
Replace with LinuxServer.io pattern that creates a new user dynamically.

#### Implementation
```bash
# NEW entrypoint.sh content
#!/bin/bash
set -e

# Set defaults
PUID=${PUID:-1000}
PGID=${PGID:-1000}

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

# Create group if it doesn't exist
if ! getent group abc >/dev/null 2>&1; then
    echo "Creating group abc with GID $PGID"
    groupadd -g "$PGID" abc
fi

# Create user if it doesn't exist
if ! getent passwd abc >/dev/null 2>&1; then
    echo "Creating user abc with UID $PUID"
    useradd -u "$PUID" -g "$PGID" -d /config -s /bin/bash abc
fi

# Set up directories with proper ownership
echo "Setting up directories..."
mkdir -p /config /downloads /downloads/.extracted_files
chown -R abc:abc /app /config /downloads

# Start application as abc user
echo "Starting application as abc (UID:$PUID, GID:$PGID)"
exec gosu abc "$@"
```

### Task 2: Update Dockerfile to Support New Pattern
**Priority**: HIGH  
**Estimated Time**: 1 hour  

#### Changes Needed
1. Remove existing `appuser` creation
2. Ensure container runs as root initially
3. Add proper gosu installation

#### Implementation
```dockerfile
# Remove these lines:
# RUN groupadd -r appuser && useradd -r -g appuser appuser
# && chown -R appuser:appuser /app

# Keep gosu installation as is
# Add config directory creation
RUN mkdir -p /config
```

### Task 3: Test with Simple Scenario
**Priority**: HIGH  
**Estimated Time**: 30 minutes  

#### Test Commands
```bash
# Build and test
docker build -t radarr-extractor:test .

# Test with custom PUID/PGID
docker run --rm -e PUID=3000 -e PGID=1000 \
    -v /tmp/test:/downloads \
    radarr-extractor:test

# Verify user and permissions
docker exec <container> id abc
docker exec <container> ls -la /downloads
```

### Task 4: Update docker-compose.yml
**Priority**: MEDIUM  
**Estimated Time**: 15 minutes  

#### Changes Needed
```yaml
# Add config volume
volumes:
  - ${DOWNLOAD_VOLUME}:/downloads
  - ./config:/config  # Add this line
```

### Task 5: Update Health Check
**Priority**: MEDIUM  
**Estimated Time**: 15 minutes  

#### Changes Needed
```dockerfile
# Update health check to use abc user
HEALTHCHECK --interval=5m --timeout=3s \
    CMD gosu abc python -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(("127.0.0.1", 9898)); s.close();'
```

## Critical Success Factors

### 1. User Creation Strategy
- **OLD**: Modify existing `appuser` (999:999) → **FAILS**
- **NEW**: Create new `abc` user with specified PUID/PGID → **WORKS**

### 2. Execution Flow
1. Container starts as root
2. Create group/user with PUID/PGID
3. Set directory ownership
4. Switch to `abc` user using gosu
5. Run application

### 3. Directory Structure
```
/app/          # Application files (owned by abc:abc)
/config/       # Configuration files (owned by abc:abc)
/downloads/    # Downloads volume (owned by abc:abc)
```

## Quick Fix Implementation

### 1. Replace entrypoint.sh
```bash
# Save the new entrypoint.sh content above
# This should resolve the permission issues immediately
```

### 2. Update Dockerfile
```dockerfile
# Remove appuser creation lines
# Add mkdir -p /config
# Keep gosu installation
```

### 3. Test and Deploy
```bash
# Build
./docker-build.sh

# Test locally
docker run --rm -e PUID=3000 -e PGID=1000 -v /tmp/test:/downloads radarr-extractor:test

# Deploy if successful
```

## Expected Results

After implementing these changes:

1. **No more permission errors**: Container will run as specified PUID/PGID
2. **Proper file ownership**: Files created will have correct host ownership
3. **Reliable startup**: No more "Permission denied" or "cannot lock" errors
4. **LinuxServer.io compatibility**: Follows established patterns users expect

## Verification Commands

```bash
# Check container user
docker exec <container> id abc

# Check file permissions
docker exec <container> ls -la /downloads

# Check process ownership
docker exec <container> ps aux

# Test file creation
docker exec <container> touch /downloads/test.txt
ls -la /path/to/host/downloads/test.txt
```

This implementation follows the LinuxServer.io standard and should resolve all current PUID/PGID issues.