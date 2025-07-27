# PUID/PGID Support - Product Requirements Document

## Overview

This PRD outlines the implementation of PUID (Process User ID) and PGID (Process Group ID) support for the radarr-extractor Docker container to resolve file permission issues when mounting host directories.

## Problem Statement

### Current Issue
The radarr-extractor Docker container currently runs as a hardcoded user (uid=999/gid=999 - appuser), which causes permission problems when:
- Mounting host directories as volumes
- The host user has different UID/GID than the container user
- Files created by the container cannot be accessed by the host user
- Files on the host cannot be accessed by the container user

### Impact
- Users experience permission denied errors when the container tries to extract files
- Files created by the container are owned by uid=999/gid=999, making them inaccessible to host users
- Manual permission fixes are required after each container run
- Poor user experience for homelab and self-hosted deployments

## Solution Requirements

### Functional Requirements

#### FR1: Environment Variable Support
- The container MUST accept `PUID` and `PGID` environment variables
- Default values: `PUID=1000` and `PGID=1000`
- Values MUST be applied at container startup

#### FR2: User Permission Mapping
- The container MUST run the application process with the specified PUID/PGID
- The application MUST have read/write access to mounted volumes
- File operations MUST use the specified user permissions

#### FR3: Directory Ownership
- The container MUST set proper ownership for:
  - Application directory (`/app`)
  - Downloads directory (`/downloads`)
  - Extracted files directory (`/downloads/.extracted_files`)
- Ownership MUST match the specified PUID/PGID

#### FR4: Backward Compatibility
- Existing deployments without PUID/PGID variables MUST continue to work
- Default behavior MUST be safe and functional

### Non-Functional Requirements

#### NFR1: Security
- The container MUST NOT run the application as root
- User switching MUST be performed securely using established tools
- No privilege escalation vulnerabilities

#### NFR2: Reliability
- The container MUST start successfully even if user modification fails
- Error handling MUST be robust and provide clear error messages
- Container restart behavior MUST be consistent

#### NFR3: Performance
- User switching overhead MUST be minimal
- Container startup time MUST not significantly increase
- Runtime performance MUST be unaffected

## Technical Implementation

### Architecture Overview
```
Container Startup Flow:
1. Container starts as root
2. Entrypoint script executes
3. User/group creation/modification
4. Directory ownership setup
5. Switch to target user using gosu
6. Execute application
```

### Components

#### 1. Entrypoint Script (`entrypoint.sh`)
- **Purpose**: Handle PUID/PGID processing and user switching
- **Responsibilities**:
  - Parse environment variables
  - Create/modify user and group
  - Set directory permissions
  - Switch to target user
  - Execute application

#### 2. Dockerfile Updates
- **Purpose**: Install required tools and configure container
- **Changes**:
  - Install `gosu` for secure user switching
  - Set entrypoint script as container entry point
  - Ensure container runs as root initially

#### 3. Docker Compose Configuration
- **Purpose**: Provide easy configuration for users
- **Changes**:
  - Add PUID/PGID environment variables
  - Set sensible defaults
  - Document usage

### Implementation Details

#### User Management Strategy
1. **Check Current User**: Determine existing appuser UID/GID
2. **Modify if Needed**: Use `usermod`/`groupmod` to change UID/GID
3. **Fallback Strategy**: Delete and recreate user/group if modification fails
4. **Switch User**: Use `gosu` to execute application as target user

#### Error Handling
- Graceful fallback if user modification fails
- Clear error messages for troubleshooting
- Container continues to run with default user if PUID/PGID setup fails

## Testing Requirements

### Test Scenarios

#### TS1: Default Behavior
- Container starts without PUID/PGID variables
- Application runs as default user (1000:1000)
- All functionality works as expected

#### TS2: Custom PUID/PGID
- Container starts with PUID=3000 and PGID=1000
- Application runs with specified user permissions
- Files created have correct ownership

#### TS3: Permission Scenarios
- Test with various host user scenarios
- Verify file access and creation permissions
- Test with different mount point configurations

#### TS4: Error Scenarios
- Test with invalid PUID/PGID values
- Test with conflicting system users
- Verify graceful degradation

## Success Criteria

### Primary Success Metrics
1. **Permission Issues Resolved**: No more permission denied errors with mounted volumes
2. **User Adoption**: Existing users can easily migrate to new version
3. **File Ownership**: Files created by container have correct host user ownership

### Secondary Success Metrics
1. **Documentation**: Clear usage instructions and troubleshooting guides
2. **Community Feedback**: Positive response from users experiencing permission issues
3. **Stability**: No regression in existing functionality

## Rollout Plan

### Phase 1: Development and Testing
- Implement entrypoint script and Dockerfile changes
- Test with various scenarios and configurations
- Update documentation

### Phase 2: Release
- Build and publish updated Docker image
- Update README with PUID/PGID documentation
- Announce changes to users

### Phase 3: Support
- Monitor for user feedback and issues
- Provide troubleshooting support
- Iterate on implementation based on feedback

## Risks and Mitigation

### Risk 1: User Modification Failures
- **Mitigation**: Implement robust fallback mechanisms
- **Fallback**: Continue with default user if modification fails

### Risk 2: Security Vulnerabilities
- **Mitigation**: Use established tools (gosu) for user switching
- **Validation**: Security review of entrypoint script

### Risk 3: Compatibility Issues
- **Mitigation**: Maintain backward compatibility
- **Testing**: Comprehensive testing with existing configurations

## Documentation Updates

### Required Documentation
1. **README.md**: Add PUID/PGID configuration section
2. **Docker Compose Examples**: Show usage with PUID/PGID
3. **Troubleshooting Guide**: Common permission issues and solutions
4. **Migration Guide**: Help existing users adopt new features

### Documentation Locations
- Main README.md
- Docker Hub description
- GitHub wiki/documentation
- CLAUDE.md development guide

## Future Enhancements

### Potential Improvements
1. **Advanced Permission Mapping**: Support for additional permission scenarios
2. **Automatic Detection**: Detect host user from mounted volumes
3. **Multi-User Support**: Support for multiple user mappings
4. **Integration**: Better integration with *arr application ecosystems

---

**Document Version**: 1.0  
**Last Updated**: 2025-07-07  
**Status**: Implementation In Progress