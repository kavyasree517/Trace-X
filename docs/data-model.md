# Data model specification

## Core entities

### cases
Tracks victim incident reports and analysis jobs.
- `id`: UUID primary key
- `case_reference`: Unique public identifier (format: TX-YYYY-NNNNNN)
- `access_token_hash`: SHA-256 hash of 128-bit secret token
- `chain`: Blockchain identifier (e.g., ethereum)
- `reported_address`: Canonical EIP-55 suspect address
- `reported_tx_hash`: Optional anchoring transaction hash
- `incident_date`: Reported date of incident
- `incident_date_precision`: exact, day, approximate, unknown
- `reported_amount`: Reported monetary amount
- `reported_asset`: Asset symbol or contract address
- `status`: pending, running, completed, partial, failed
- `parameters`: JSONB dictionary of analysis parameters
- `data_snapshot_id`: Identifier of underlying chain snapshot
- `code_version`: Version string of analysis software
- `model_version`: Version string of signal evaluation model
- `is_demo`: Boolean flag indicating demonstration data
- `analysis_started_at`: UTC timestamp of analysis start
- `analysis_completed_at`: UTC timestamp of analysis completion
- `failure_reason`: Error description if status is failed

### case_private_details
Stores sensitive user data separately with application-level encryption.
- `case_id`: UUID foreign key to cases.id
- `narrative_ciphertext`: AES-256-GCM encrypted incident narrative
- `contact_ciphertext`: AES-256-GCM encrypted contact reference
- `consent_recorded`: Boolean indicating explicit user consent
- `retention_until`: UTC deletion deadline

### transactions
Immutable table of observed on-chain transfer events.
- `id`: UUID primary key
- `chain`: Blockchain identifier
- `tx_hash`: 64-character hex transaction hash
- `log_index`: Event log index (-1 for native or internal transfers)
- `transfer_kind`: native, internal, token
- `block_number`: Integer block height
- `block_timestamp`: UTC block timestamp
- `sender`: Canonical sender address
- `receiver`: Canonical receiver address
- `asset_id`: Token contract address or "native"
- `asset_symbol`: Ticker symbol (e.g. ETH, USDT)
- `asset_decimals`: Integer decimal precision
- `amount_raw`: Numeric(78, 0) raw atomic unit
- `amount_decimal`: Decimal representation
- `status`: success, failed
- `source`: Data adapter identifier
- `retrieved_at`: UTC retrieval timestamp

### entity_labels
Provenance-tracked entity attribution labels.
- `id`: UUID primary key
- `entity_name`: Plaintext organization or service name
- `entity_type`: Controlled vocabulary type (exchange, mixer, etc.)
- `chain`: Target blockchain network
- `address`: Canonical address
- `source_name`: Publishing entity or dataset
- `source_type`: primary_disclosure, reputable_secondary, community, dataset, synthetic
- `source_reference`: Citable URL or DOI
- `verification_level`: level_3_primary_source, level_2_reputable_secondary, level_1_community_or_unverified, level_0_synthetic
- `observed_at`: Date first observed
- `last_verified_at`: Date last verified
- `is_shared_infrastructure`: Boolean flag for multi-tenant service contracts
- `is_active`: Boolean status flag
