# EPIC: PUID/PGID Permission Management System

## Epic Overview

**Epic ID**: EP-001  
**Title**: Implement PUID/PGID support for Docker container user permission management  
**Priority**: High  
**Status**: In Progress  

### Epic Description

Implement a comprehensive PUID (Process User ID) and PGID (Process Group ID) system for the radarr-extractor Docker container to resolve file permission issues when mounting host directories. This epic addresses the fundamental problem of hardcoded container user permissions that cause permission conflicts in homelab and NAS environments.

### Business Value

- **User Experience**: Eliminates permission denied errors and manual file ownership fixes
- **Security**: Maintains non-root execution while providing flexible user mapping
- **Compatibility**: Ensures seamless operation across different host environments
- **Maintenance**: Reduces support burden and user frustration

### Epic Goals

1. **Eliminate Permission Issues**: Container files and host files have consistent ownership
2. **Provide Flexible User Mapping**: Users can specify any UID/GID for their environment
3. **Maintain Security**: Container never runs application as root
4. **Ensure Reliability**: Robust error handling and fallback mechanisms

### Acceptance Criteria

- [ ] Container accepts PUID and PGID environment variables
- [ ] Application process runs with specified UID/GID
- [ ] Files created by container have correct ownership on host
- [ ] Backward compatibility maintained for existing deployments
- [ ] Comprehensive logging and troubleshooting support
- [ ] Security audit passes (no root execution of application)

### Dependencies

- Docker container runtime
- gosu or similar user-switching utility
- LinuxServer.io pattern adoption

### Risks

- **High**: User modification failures in constrained environments
- **Medium**: Performance impact from user switching overhead
- **Low**: Compatibility issues with existing deployments

---

## User Stories

### Story 1: Core PUID/PGID Support

**Story ID**: US-001  
**Title**: As a container user, I want to specify PUID and PGID so that my container files have the correct ownership  
**Priority**: High  
**Story Points**: 8  

#### Description
Implement the foundational PUID/PGID environment variable support that allows users to specify the user ID and group ID for the container process.

#### Acceptance Criteria
- [ ] Container accepts PUID environment variable (default: 1000)
- [ ] Container accepts PGID environment variable (default: 1000)
- [ ] Environment variables are validated (numeric, positive integers)
- [ ] Invalid values log warnings and use defaults
- [ ] Variables are applied at container startup

#### Technical Tasks
- [ ] Create entrypoint script with environment variable parsing
- [ ] Add input validation for PUID/PGID values
- [ ] Implement default value fallback logic
- [ ] Add logging for variable values and validation results

---

### Story 2: Secure User Creation and Switching

**Story ID**: US-002  
**Title**: As a security-conscious user, I want the container to run as non-root with my specified UID/GID  
**Priority**: High  
**Story Points**: 13  

#### Description
Implement secure user creation and switching mechanism that creates a new user with specified UID/GID and switches to that user before running the application.

#### Acceptance Criteria
- [ ] Container starts as root for user management
- [ ] Creates new user with specified PUID/PGID
- [ ] Switches to new user before executing application
- [ ] Application never runs as root
- [ ] User creation failures are handled gracefully

#### Technical Tasks
- [ ] Install gosu for secure user switching
- [ ] Create user/group creation logic
- [ ] Implement user switching in entrypoint script
- [ ] Add error handling for user creation failures
- [ ] Create fallback mechanisms for edge cases

---

### Story 3: Directory Ownership Management

**Story ID**: US-003  
**Title**: As a homelab user, I want all container directories to have correct ownership so files are accessible  
**Priority**: High  
**Story Points**: 5  

#### Description
Ensure all critical directories have proper ownership set to the specified PUID/PGID, including application directory, downloads directory, and extracted files directory.

#### Acceptance Criteria
- [ ] /app directory ownership matches PUID/PGID
- [ ] /downloads directory ownership matches PUID/PGID  
- [ ] /downloads/.extracted_files directory created with correct ownership
- [ ] Ownership is set before switching to target user
- [ ] Recursive ownership setting for nested directories

#### Technical Tasks
- [ ] Implement directory ownership setting logic
- [ ] Create .extracted_files directory with proper permissions
- [ ] Add recursive ownership setting for existing files
- [ ] Handle mounted volumes with existing files
- [ ] Add verification of ownership setting success

---

### Story 4: Backward Compatibility

**Story ID**: US-004  
**Title**: As an existing user, I want my current deployment to continue working without PUID/PGID variables  
**Priority**: Medium  
**Story Points**: 3  

#### Description
Ensure existing deployments without PUID/PGID environment variables continue to function normally with default behavior.

#### Acceptance Criteria
- [ ] Container works without PUID/PGID variables
- [ ] Default values (1000:1000) are applied
- [ ] No breaking changes to existing functionality
- [ ] Existing docker-compose files continue to work
- [ ] Health checks continue to pass

#### Technical Tasks
- [ ] Test existing deployments without variables
- [ ] Verify default behavior with 1000:1000
- [ ] Ensure health checks work with new user switching
- [ ] Test with various Docker orchestration tools

---

### Story 5: Comprehensive Logging and Troubleshooting

**Story ID**: US-005  
**Title**: As a troubleshooting user, I want detailed logs to diagnose permission issues  
**Priority**: Medium  
**Story Points**: 5  

#### Description
Implement comprehensive logging that helps users diagnose permission issues and verify that PUID/PGID settings are applied correctly.

#### Acceptance Criteria
- [ ] Log PUID/PGID values being applied
- [ ] Log user creation/modification results
- [ ] Log directory ownership changes
- [ ] Log user switching operations
- [ ] Provide troubleshooting commands in logs

#### Technical Tasks
- [ ] Add structured logging throughout entrypoint script
- [ ] Create diagnostic output for user verification
- [ ] Add error-specific troubleshooting hints
- [ ] Implement log levels for different verbosity needs
- [ ] Create troubleshooting documentation

---

### Story 6: Docker Compose Integration

**Story ID**: US-006  
**Title**: As a Docker Compose user, I want easy PUID/PGID configuration examples  
**Priority**: Medium  
**Story Points**: 2  

#### Description
Provide clear Docker Compose examples and .env file templates that make PUID/PGID configuration straightforward for users.

#### Acceptance Criteria
- [ ] docker-compose.yml includes PUID/PGID variables
- [ ] .env file includes PUID/PGID defaults
- [ ] Examples show how to find user's UID/GID
- [ ] Documentation explains common use cases
- [ ] Integration with existing compose setup

#### Technical Tasks
- [ ] Update docker-compose.yml with PUID/PGID variables
- [ ] Create .env template with explanations
- [ ] Add comments explaining variable usage
- [ ] Test compose configuration with various scenarios
- [ ] Update README with compose examples

---

### Story 7: Performance and Reliability

**Story ID**: US-007  
**Title**: As a performance-conscious user, I want PUID/PGID to have minimal impact on container performance  
**Priority**: Low  
**Story Points**: 3  

#### Description
Optimize the PUID/PGID implementation to minimize startup time and runtime performance impact while maintaining reliability.

#### Acceptance Criteria
- [ ] Container startup time increase < 2 seconds
- [ ] Runtime performance unaffected
- [ ] Memory usage increase < 10MB
- [ ] Reliable operation across container restarts
- [ ] No resource leaks from user switching

#### Technical Tasks
- [ ] Benchmark container startup times
- [ ] Optimize user creation/switching logic
- [ ] Implement caching for repeated operations
- [ ] Add performance monitoring
- [ ] Test reliability across multiple restart cycles

---

### Story 8: Documentation and Migration Guide

**Story ID**: US-008  
**Title**: As a new user, I want clear documentation on how to use PUID/PGID functionality  
**Priority**: Low  
**Story Points**: 3  

#### Description
Create comprehensive documentation that explains PUID/PGID functionality, common use cases, troubleshooting, and migration from previous versions.

#### Acceptance Criteria
- [ ] README section explaining PUID/PGID
- [ ] Troubleshooting guide with common issues
- [ ] Migration guide for existing users
- [ ] Examples for different environments (TrueNAS, Portainer, etc.)
- [ ] Security considerations documented

#### Technical Tasks
- [ ] Update README with PUID/PGID section
- [ ] Create troubleshooting documentation
- [ ] Write migration guide for existing users
- [ ] Add environment-specific examples
- [ ] Document security best practices

---

## Epic Timeline

### Phase 1: Foundation (Stories 1-3)
- **Duration**: 2-3 days
- **Focus**: Core PUID/PGID implementation
- **Deliverables**: Working PUID/PGID support

### Phase 2: Reliability (Stories 4-5)
- **Duration**: 1-2 days  
- **Focus**: Backward compatibility and logging
- **Deliverables**: Production-ready implementation

### Phase 3: Polish (Stories 6-8)
- **Duration**: 1-2 days
- **Focus**: Documentation and examples
- **Deliverables**: Complete user experience

## Success Metrics

- **Functional**: 0 permission denied errors with proper PUID/PGID configuration
- **User Experience**: < 5 minutes to configure PUID/PGID for new users
- **Security**: 0 vulnerabilities in security audit
- **Performance**: < 2 second startup time overhead
- **Adoption**: 80% of users migrate to PUID/PGID within 30 days

## Definition of Done

- [ ] All acceptance criteria met for all stories
- [ ] Code review completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Backward compatibility verified
- [ ] Docker image built and published
- [ ] User testing completed successfully