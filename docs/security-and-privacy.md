# Security and privacy controls

## Security architecture

### Input validation and sanitization
- Canonical address formatting: EIP-55 checksum enforced at API perimeter.
- Transaction hashes: Strict 64-character lowercase hex verification.
- Timestamps: ISO 8601 validation rejecting future timestamps.
- Request payload limiting: Maximum request body capped at 16,384 bytes.

### Secrets management
- Secrets are loaded exclusively via environment variables into typed configuration (`core/config.py`).
- API keys, database credentials, and symmetric encryption keys are excluded from all logging and API responses.
- Automated secret scanning is enforced in pre-commit hooks and continuous integration.

### Transport and network security
- Security headers: HSTS, Content-Security-Policy (CSP), X-Content-Type-Options: nosniff, Referrer-Policy: no-referrer, X-Frame-Options: DENY.
- CORS policy: Explicit origins allowlist, no wildcard in production.

### Access control and roles
- Public tier: Create case, read case summary via 128-bit access reference, label lookup, health checks.
- Investigator tier: Authenticated via bearer token for audit trail verification and consented narrative access.
- Administrator tier: Authenticated via bearer token for reference label management and system maintenance.

### Data privacy and retention
- Personal details separation: Incident narrative and contact information are encrypted at application level using AES-256-GCM and stored in isolated tables.
- Automated retention job: Prunes expired case records (180 days default) and generated PDF reports (90 days default), recording immutable `case_deleted` audit events.
