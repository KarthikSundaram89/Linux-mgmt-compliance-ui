# Security Guide

## Overview

The Linux Inventory Manager is designed to pass enterprise SAST and DAST (WASA) security reviews with zero Critical or High vulnerabilities.

## OWASP Top 10 Coverage

| OWASP Risk | Mitigation |
|-----------|-----------|
| A01 Broken Access Control | RBAC on all endpoints, never trust client-side |
| A02 Cryptographic Failures | Argon2/bcrypt passwords, TLS enforced, no secrets on disk |
| A03 Injection | SQLAlchemy ORM (parameterized), SSH command allowlist |
| A04 Insecure Design | Clean Architecture, least privilege, defense in depth |
| A05 Security Misconfiguration | Hardened defaults, security headers, no debug in prod |
| A06 Vulnerable Components | Pinned deps, SBOM, regular updates |
| A07 Auth Failures | Account lockout, password policy, JWT expiration |
| A08 Data Integrity | SHA-256 checksums on snapshots, audit trail |
| A09 Logging Failures | Structured logging, audit log, secret masking |
| A10 SSRF | No outbound user-controlled requests, allowlist commands |

## Command Injection Protection

**Highest Risk Area:** SSH command execution on remote servers.

Mitigations:
- `COMMAND_ALLOWLIST` frozenset - only predefined commands execute
- `PARAMETERIZED_COMMAND_PREFIXES` for safe parameterized commands
- `SecurityError` raised for any non-allowlisted command
- No user-supplied commands are ever executed
- No terminal/shell interface exposed
- No SSH execution API endpoints
- Arguments are never concatenated into shell commands

## Authentication Security

- Passwords hashed with Argon2id (bcrypt fallback)
- Minimum 12 characters, complexity enforced
- Password history prevents reuse (last 5)
- Account lockout after 5 failed attempts
- JWT tokens with configurable expiration
- Refresh token rotation
- Session timeout (idle + absolute)

## Authorization

- RBAC enforced on EVERY REST endpoint
- Three roles: Administrator, Operator, Read Only
- Permission-based granular access (resource + action)
- Never rely on UI restrictions alone
- API returns 403 for unauthorized operations

## Input Validation

- All inputs validated server-side (Pydantic models)
- Sort fields validated against allowlist (prevent SQL injection)
- Pagination parameters bounded
- Hostname/IP/UUID format validation
- XSS patterns rejected (script tags, event handlers)
- Request body size limited (10 MB)
- File upload type/size validation

## HTTP Security Headers

All responses include:
- `Content-Security-Policy` (strict, no unsafe-inline scripts)
- `Strict-Transport-Security` (HSTS with preload)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` (camera, microphone, geolocation disabled)
- `Cache-Control: no-store` on authenticated responses

## Rate Limiting

- Token bucket algorithm per client IP
- Login endpoint: 5 requests/minute
- General API: 60 requests/minute
- Bulk operations: 10 requests/minute
- Report generation: 5 requests/minute
- Returns 429 with Retry-After header

## Secrets Management

**Secrets are NEVER stored in:**
- SQLite database
- Configuration files on disk
- Log files
- API responses
- Browser localStorage
- HTML/JavaScript source

**Secrets storage:** AWS Secrets Manager only.
Retrieved at runtime, held in memory, never persisted.

## Audit Trail

Every significant action is recorded:
- Authentication events
- Data modifications
- Administrative actions
- Collection events

Each entry includes: timestamp, user, action, target, IP, outcome.

## Error Handling

- Stack traces never exposed to clients
- Generic error messages returned
- Detailed errors logged server-side only
- No database error details in responses
- No filesystem paths revealed

## File Upload Security

- Allowed extensions: .csv, .json, .txt only
- Content-type validation
- Size limits enforced
- Random filename generation
- Directory traversal prevention
- CSV injection character escaping

## SSH Connection Security

- Host key validation (RejectPolicy)
- Known hosts file required
- Connection timeout enforcement
- Idle connection cleanup
- Maximum pool size limits
- No insecure algorithms
- Private keys from Secrets Manager only
