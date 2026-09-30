# API specification

## Base URL
All API v1 endpoints are served under `/api/v1`.

## Protocol standards
- Format: JSON request and response payloads.
- Naming convention: snake_case for all field keys.
- Timestamp format: ISO 8601 extended UTC with trailing Z (e.g. 2026-09-30T08:00:00Z).
- Tracing header: `X-Request-ID` is generated or echoed on every request.

## Uniform error response
All client and server errors return HTTP status with the following structure:
```json
{
  "error": {
    "code": "invalid_address",
    "message": "The provided address is not a valid EIP-55 Ethereum address.",
    "field": "address",
    "request_id": "req-9b8c7d6e"
  }
}
```

### Standard error codes
- `invalid_address`: Address format or checksum failure
- `invalid_chain`: Specified blockchain network is unsupported
- `invalid_tx_hash`: Transaction hash malformed
- `invalid_date`: Incident date in future or unparseable
- `limit_exceeded`: Request parameter exceeds hard system limit
- `rate_limited`: Client rate limit exceeded (includes Retry-After header)
- `upstream_unavailable`: Blockchain provider unreachable
- `upstream_timeout`: Blockchain provider exceeded response deadline
- `case_not_found`: Case reference does not exist
- `report_not_ready`: Analysis still in progress
- `internal_error`: Unhandled server exception

## Endpoints summary
- `GET /health`: Basic service liveness check
- `GET /health/ready`: Service dependency and database readiness check
- `POST /cases`: Submit reported address and incident parameters for analysis
- `GET /cases/{reference}`: Retrieve case summary, progress stages, and confidence panel
- `GET /cases/{reference}/paths`: Retrieve ranked fund movement paths and edge tables
- `GET /cases/{reference}/attributions`: Retrieve matched entity attributions and factors
- `GET /cases/{reference}/signals`: Retrieve extracted behavioral signals
- `GET /cases/{reference}/related`: Retrieve corroborated cases and shared evidence
- `POST /cases/{reference}/refresh`: Trigger re-analysis against updated chain data
- `GET /cases/{reference}/report.pdf`: Download immutable forensic evidence dossier
- `GET /cases/{reference}/audit`: Retrieve cryptographically verifiable audit trail
- `GET /labels/{chain}/{address}`: Inspect entity registry labels for an address
