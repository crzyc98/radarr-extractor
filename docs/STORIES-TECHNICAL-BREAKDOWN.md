# Technical Story Breakdown - PUID/PGID Implementation

## Story Implementation Details

### US-001: Core PUID/PGID Support

#### Implementation Strategy
Follow LinuxServer.io patterns for consistent user experience across homelab containers.

#### Technical Implementation
```bash
# Environment variable parsing with validation
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Validation logic
if ! [[ "$PUID" =~ ^[0-9]+$ ]] || [ "$PUID" -eq 0 ]; then
    echo "WARNING: Invalid PUID=$PUID, using default 1000"
    PUID=1000
fi

if ! [[ "$PGID" =~ ^[0-9]+$ ]] || [ "$PGID" -eq 0 ]; then
    echo "WARNING: Invalid PGID=$PGID, using default 1000"
    PGID=1000
fi
```

#### Files to Modify
- `entrypoint.sh` - Add environment variable parsing and validation
- `Dockerfile` - Ensure proper entrypoint setup

#### Testing Scenarios
- Valid PUID/PGID values (1000, 1001, 3000, etc.)
- Invalid values (0, negative, non-numeric, empty)
- Missing environment variables
- Edge cases (very large numbers)

---

### US-002: Secure User Creation and Switching

#### Implementation Strategy
Create a new user dynamically instead of modifying existing users. This avoids permission issues and follows security best practices.

#### Technical Implementation
```bash
# Create group first
if ! getent group abc >/dev/null; then
    groupadd -g "$PGID" abc
fi

# Create user
if ! getent passwd abc >/dev/null; then
    useradd -u "$PUID" -g "$PGID" -d /config -s /bin/bash abc
fi

# Switch to user using gosu
exec gosu abc "$@"
```

#### Architecture Decision
- Use LinuxServer.io naming convention (`abc` user)
- Create user with home directory in `/config`
- Use `gosu` for secure privilege dropping
- Handle existing user/group conflicts gracefully

#### Files to Modify
- `entrypoint.sh` - Add user creation logic
- `Dockerfile` - Install gosu, ensure proper permissions

#### Security Considerations
- Never run application as root
- Use `gosu` instead of `su` for security
- Validate UID/GID ranges to prevent system user conflicts
- Ensure proper signal handling for container shutdown

---

### US-003: Directory Ownership Management

#### Implementation Strategy
Set ownership before switching users to ensure proper permissions for all application directories.

#### Technical Implementation
```bash
# Directories that need proper ownership
DIRS_TO_OWN=(
    "/app"
    "/downloads"
    "/config"
)

# Create and set ownership
for dir in "${DIRS_TO_OWN[@]}"; do
    mkdir -p "$dir"
    chown -R abc:abc "$dir"
done

# Special handling for extracted files directory
mkdir -p /downloads/.extracted_files
chown abc:abc /downloads/.extracted_files
```

#### Edge Cases to Handle
- Mounted volumes with existing files
- Read-only mounts
- Nested directory structures
- Symlinks and special files

#### Files to Modify
- `entrypoint.sh` - Add directory ownership logic
- Application code - Ensure proper directory creation

---

### US-004: Backward Compatibility

#### Implementation Strategy
Ensure all changes are additive and don't break existing functionality.

#### Compatibility Matrix
| Scenario | PUID | PGID | Expected Behavior |
|----------|------|------|-------------------|
| Current users | Not set | Not set | Use defaults (1000:1000) |
| Partial config | Set | Not set | Use PUID, default PGID |
| Full config | Set | Set | Use both values |
| Invalid config | Invalid | Invalid | Use defaults, log warnings |

#### Testing Requirements
- Test with existing docker-compose files
- Verify health checks still pass
- Ensure no breaking changes to API
- Test with various Docker orchestrators

---

### US-005: Comprehensive Logging and Troubleshooting

#### Implementation Strategy
Provide structured logging that helps users diagnose and resolve permission issues.

#### Logging Structure
```bash
echo "=========================================="
echo "PUID/PGID Configuration"
echo "=========================================="
echo "Environment variables:"
echo "  PUID: $PUID"
echo "  PGID: $PGID"
echo "User creation:"
echo "  User: abc (UID: $PUID, GID: $PGID)"
echo "Directory ownership:"
echo "  /app: $(ls -ld /app | awk '{print $3":"$4}')"
echo "  /downloads: $(ls -ld /downloads | awk '{print $3":"$4}')"
echo "Troubleshooting:"
echo "  Host: Run 'id \$USER' to find your UID/GID"
echo "  Container: Run 'docker exec <container> id abc'"
echo "=========================================="
```

#### Troubleshooting Commands
Include helpful commands in logs for user self-service:
- How to find host UID/GID
- How to verify container user
- How to check file permissions
- Common permission fix commands

---

### US-006: Docker Compose Integration

#### Implementation Strategy
Provide ready-to-use Docker Compose configuration with clear examples.

#### Docker Compose Template
```yaml
version: "3.8"
services:
  radarr-extractor:
    image: crzyc/radarr-extractor:latest
    container_name: radarr-extractor
    environment:
      - PUID=${PUID:-1000}
      - PGID=${PGID:-1000}
      - RADARR_URL=${RADARR_URL}
      - RADARR_API_KEY=${RADARR_API_KEY}
    volumes:
      - ${DOWNLOAD_VOLUME}:/downloads
      - ./config:/config
    restart: unless-stopped
```

#### .env Template
```bash
# User Configuration
# Run 'id $USER' to find your UID and GID
PUID=1000
PGID=1000

# Radarr Configuration
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_api_key_here

# Volume Configuration
DOWNLOAD_VOLUME=/path/to/downloads
```

---

### US-007: Performance and Reliability

#### Implementation Strategy
Optimize the implementation for minimal overhead while maintaining reliability.

#### Performance Optimizations
- Cache user lookups to avoid repeated calls
- Minimize file system operations
- Use efficient ownership setting commands
- Implement early exit for no-op scenarios

#### Reliability Measures
- Implement retry logic for transient failures
- Add health checks for user switching
- Handle signal propagation correctly
- Ensure graceful shutdown

#### Monitoring Points
```bash
# Performance metrics to track
START_TIME=$(date +%s)
# ... user creation logic ...
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "PUID/PGID setup completed in ${DURATION}s"
```

---

### US-008: Documentation and Migration Guide

#### Documentation Structure
```
docs/
├── PUID-PGID-GUIDE.md           # User guide
├── TROUBLESHOOTING.md           # Common issues and solutions
├── MIGRATION-GUIDE.md           # Migration from previous versions
├── SECURITY-CONSIDERATIONS.md   # Security best practices
└── EXAMPLES/
    ├── docker-compose.yml       # Basic compose example
    ├── docker-compose.advanced.yml  # Advanced configuration
    ├── truenas-scale.yml        # TrueNAS SCALE specific
    └── portainer-stack.yml      # Portainer stack configuration
```

#### Migration Guide Content
- How to upgrade from previous versions
- What changes for existing users
- How to troubleshoot common migration issues
- Best practices for new deployments

---

## Implementation Order

### Phase 1: Core Implementation (US-001, US-002, US-003)
1. **Day 1**: Implement environment variable parsing and validation
2. **Day 2**: Implement user creation and switching logic
3. **Day 3**: Implement directory ownership management
4. **Day 4**: Integration testing and bug fixes

### Phase 2: Reliability and Compatibility (US-004, US-005)
1. **Day 5**: Implement backward compatibility checks
2. **Day 6**: Add comprehensive logging and troubleshooting
3. **Day 7**: Testing with various scenarios

### Phase 3: Polish and Documentation (US-006, US-007, US-008)
1. **Day 8**: Update Docker Compose and examples
2. **Day 9**: Performance optimization and reliability testing
3. **Day 10**: Documentation and migration guide

## Quality Gates

### Before Phase 2
- [ ] Core PUID/PGID functionality works
- [ ] Basic user creation and switching operational
- [ ] Directory ownership correctly set
- [ ] No security vulnerabilities

### Before Phase 3
- [ ] Backward compatibility verified
- [ ] Comprehensive logging implemented
- [ ] Error handling robust
- [ ] Performance benchmarks met

### Before Release
- [ ] All acceptance criteria met
- [ ] Documentation complete
- [ ] Migration guide tested
- [ ] Security audit passed
- [ ] Performance requirements met

## Testing Strategy

### Unit Tests
- Environment variable parsing
- User creation logic
- Directory ownership functions
- Error handling scenarios

### Integration Tests
- Full container startup with various PUID/PGID values
- File permission verification
- Volume mounting scenarios
- Health check functionality

### User Acceptance Tests
- New user deployment scenarios
- Existing user migration scenarios
- Common homelab configurations
- Error recovery scenarios

## Success Criteria

1. **Functional**: 100% of permission issues resolved with proper PUID/PGID configuration
2. **Performance**: < 2 second overhead for user switching
3. **Security**: 0 critical vulnerabilities in security scan
4. **Usability**: < 5 minutes for new user to configure PUID/PGID
5. **Reliability**: 99.9% successful container starts with PUID/PGID