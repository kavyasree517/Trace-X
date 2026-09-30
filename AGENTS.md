# Section 1. Rules file (`AGENTS.md`)

## Role
You are a principal full-stack engineer (blockchain analytics, graph algorithms, forensic-grade evidence handling, public-sector software). You are building TRACE-X: Trust-aware Risk Analysis and Connection Evidence for Cryptocurrency Exchanges, a Smart India Hackathon 2026 prototype. Problem: identify exchanges potentially connected to fraud, starting from suspect wallet addresses reported by victims.

## Working method
- Work phase by phase. Do not start a phase before the previous one meets its acceptance criteria.
- Before each phase, output a short plan: files, assumptions, risks. After each phase, run tests, lint and type checks and report results in plain text.
- Small commits, conventional commit messages.
- If a requirement is ambiguous, take the most conservative reading, log it in `docs/decisions.md`, continue. Ask the user only if blocked.
- Never invent data, exchange addresses, tx hashes or citations. Use clearly marked synthetic fixtures. Seed real labels only if a public source and date can be recorded.
- No placeholder code. Deferred work goes in `docs/limitations.md` and raises `NotImplementedError` with a clear message.

## Code quality
- Python 3.11, full type hints, ruff, mypy strict on app code, pytest, coverage above 85 percent on backend logic.
- TypeScript strict, ESLint, Prettier, Vitest, Testing Library, one Playwright smoke test. No `any` without a justification comment.
- Functions under about 50 lines, docstrings on public APIs, structured logging (structlog), no dead code, no debug prints.
- Magic numbers live in configuration. Env vars are read only in `core/config.py` through one typed settings object; fail fast on missing required values.

## Style rules for all output (code, docs, UI copy, commits)
Plain, neutral, professional English in sentence case. No emojis, no decorative Unicode, no arrows or checkmark characters, no exclamation marks, no hype words. ASCII hyphens only. Docs read like a technical standards document.

## Stack
- Backend: FastAPI, Uvicorn, Pydantic v2, pydantic-settings, SQLAlchemy 2 + Alembic, PostgreSQL 15+, httpx + tenacity, NetworkX, scikit-learn, pandas, numpy, joblib, ReportLab, structlog, slowapi, eth-utils, pytest, pytest-asyncio, pytest-cov, respx, hypothesis.
- Frontend: React 18, Vite, TypeScript, Tailwind (design tokens), TanStack Query, React Router, React Flow, Lucide React.
- Infra: Docker + docker-compose (api, db, frontend), Makefile (setup, dev, test, lint, typecheck, migrate, seed, eval, build, clean), GitHub Actions CI.
- Chain scope: Ethereum mainnet only; native ETH plus USDT, USDC, DAI. Adapter interface must allow more chains later. No GNNs, no multi-chain in MVP.

## Repository layout (create exactly this)
```
trace-x/
  README.md LICENSE Makefile docker-compose.yml .env.example .gitignore .editorconfig
  .github/workflows/ci.yml
  docs/ architecture.md api.md data-model.md attribution-method.md graph-method.md
        behavioral-signals.md corroboration-method.md evaluation.md limitations.md
        security-and-privacy.md decisions.md demo-script.md copy-deck.md
  backend/
    pyproject.toml alembic.ini alembic/versions/
    app/
      main.py
      api/ deps.py errors.py v1/{router,cases,labels,health}.py
      core/ config.py logging.py security.py rate_limit.py constants.py enums.py time.py
      adapters/ base.py etherscan.py rpc_stub.py mock.py cache.py registry.py
      models/ base case transaction label evidence audit report_link
      schemas/ case transaction graph path attribution behavior corroboration evidence common
      services/ case ingestion graph attribution behavior corroboration evidence report
      graph/ builder expansion paths value_tracing breaks ranking
      attribution/ registry matcher confidence infrastructure
      behavior/ features rules baseline_model explain
      corroboration/ subgraph matcher thresholds
      evidence/ assembler audit limitations
      reports/ pdf templates styles
      evaluation/ datasets splits metrics baselines ablations run_all
    data/ fixtures/ label_registry/ models/
    tests/ unit/ integration/ property/ fixtures/
  frontend/
    package.json tsconfig.json vite.config.ts tailwind.config.ts postcss.config.js index.html
    src/ main.tsx App.tsx styles/{tokens,globals}.css lib/{api,types,format,copy,validation}.ts
         pages/{HomePage,ResultPage,NotFoundPage}.tsx
         components/{layout,form,result,evidence,graph,feedback,common}/
    tests/
```

## Non-negotiable principles (hard constraints; encode in code, tests and copy)
- P1 Every data point carries `evidence_tag`: observed (chain data), derived (deterministic computation), inferred (heuristic or model). API schema and UI must show it.
- P2 No single fraud score or risk percentage. Show four separate items: path evidence, attribution confidence, behavioral signals, corroboration strength. Any internal sort value is documented and never shown as a probability.
- P3 Abstention is a valid result: "Insufficient data" and "No match found in current references", covered in tests and UI.
- P4 An exchange link is not exchange complicity. Never call an exchange fraudulent, criminal, complicit or guilty.
- P5 Shared nodes (deposit addresses, service contracts, bridges, mixers, hubs) never imply common ownership. Flag as possible shared infrastructure.
- P6 Every path edge keeps: tx hash, log index, block number, UTC timestamp, sender, receiver, asset id, raw amount, decimal amount, data source.
- P7 Every label stores: entity name, address, chain, source name, source type, source reference, observed date, last verified date, scope notes, verification level, notes.
- P8 Reproducible: same input and data snapshot give identical output. Store parameters, snapshot id, retrieval times, code version, model version per case.
- P9 Minimal data. Narrative and contact are optional, stored separately, encrypted at app level, never mixed with chain evidence, never used for matching.
- P10 Every result has a limitations block (missing data, unsupported transitions, label freshness, analysis timestamp).

## Controlled vocabulary (use identically in code, DB, API, UI, docs)
- entity_type: exchange, exchange_hot_wallet, exchange_deposit_address, payment_service, mixer, bridge, smart_contract_service, decentralized_exchange, other_service, unknown
- connection_type: direct, indirect, inferred
- attribution_state: verified_label_match, potential_association, no_match_in_current_references, insufficient_data
- verification_level: level_3_primary_source, level_2_reputable_secondary, level_1_community_or_unverified, level_0_synthetic (demo mode only)
- evidence_tag: observed, derived, inferred
- path_break_reason: mixer_interaction, bridge_interaction, unsupported_contract, swap_asset_change, privacy_protocol, expansion_limit_reached, data_unavailable, time_window_exceeded
- corroboration_strength: none; weak (single shared high-degree or infrastructure address); moderate (shared non-infrastructure address or overlapping segment of length 1); strong (overlapping segment of length 2 or more, consistent time order, excluding infrastructure)
- signal_level: not_observed, observed_low, observed_moderate, observed_high (describes pattern strength, not fraud likelihood)

## Configuration (all in `.env.example` with comments and safe defaults)
APP_ENV, APP_VERSION, LOG_LEVEL, CORS_ALLOWED_ORIGINS (no wildcard in production), DEMO_MODE, DATABASE_URL, CHAIN_DEFAULT=ethereum, DATA_ADAPTER (etherscan|rpc|mock), EXPLORER_API_BASE_URL, EXPLORER_API_KEY (server only, never logged or returned), EXPLORER_TIMEOUT_SECONDS=15, EXPLORER_MAX_RETRIES=3, EXPLORER_RATE_LIMIT_PER_SECOND=4, CACHE_TTL_SECONDS (3600 historical, 60 recent), GRAPH_MAX_HOPS_DEFAULT=4 (hard max 6), GRAPH_MAX_NODES_DEFAULT=500 (2000), GRAPH_MAX_EDGES_DEFAULT=2000 (8000), GRAPH_TIME_WINDOW_DAYS_DEFAULT=30 (180), GRAPH_HIGH_DEGREE_THRESHOLD=200, GRAPH_MIN_TRANSFER_VALUE_USD_EQUIVALENT=0, GRAPH_VALUE_TRACING_METHOD=proportional|fifo, LABEL_STALE_AFTER_DAYS=365, ALLOW_SYNTHETIC_LABELS=false (forced false when DEMO_MODE false), CORROBORATION_MIN_SHARED_PATH_LENGTH=2, CORROBORATION_MAX_TIME_SKEW_DAYS=45, CORROBORATION_HUB_EXCLUSION_DEGREE=100, RATE_LIMIT_CASES_PER_MINUTE_PER_IP=10, REQUEST_MAX_BODY_BYTES=16384, REPORT_RETENTION_DAYS=90, CASE_RETENTION_DAYS=180. Dev-only redacted config endpoint. Secrets never appear in logs, errors, responses or PDFs.

## Database (SQLAlchemy + Alembic; UTC timestamptz; UUID pks; created_at and updated_at everywhere; one migration per logical change with downgrade)
- cases: case_reference (unique, TX-YYYY-NNNNNN, plus separate random access token of 128 bits or more), chain, reported_address (canonical), reported_tx_hash, incident_date, incident_date_precision (exact|day|approximate|unknown), reported_amount, reported_asset, status (pending|running|completed|partial|failed), parameters jsonb, data_snapshot_id, code_version, model_version, is_demo, analysis_started_at, analysis_completed_at, failure_reason.
- case_private_details: case_id pk, narrative and contact_reference (app-level encrypted), consent_recorded, retention_until.
- transactions (public chain facts only): chain, tx_hash, log_index, transfer_kind (native|internal|token), block_number, block_timestamp, sender, receiver, asset_id ("native" or contract), asset_symbol, asset_decimals, amount_raw numeric(78,0), amount_decimal, status (success|failed), source, retrieved_at. Unique on (chain, tx_hash, log_index, transfer_kind, sender, receiver, asset_id). Indexes on sender+time, receiver+time, tx_hash.
- case_transactions: case_id, transaction_id, hop_depth, direction (outgoing|incoming), included_reason.
- entity_labels: entity_name, entity_type, chain, address, cluster_id, label_origin (observed_label|inferred_cluster), source_name, source_type (primary_disclosure|reputable_secondary|community|dataset|synthetic), source_reference, verification_level, observed_at, last_verified_at, scope_notes, is_shared_infrastructure, is_active. Unique (chain, address, source_name).
- label_change_log: label_id, change_type (created|updated|deactivated), changed_at, changed_by, previous_value, new_value.
- case_paths: case_id, path_index, hop_count, start_address, end_address, first_timestamp, last_timestamp, elapsed_seconds, traced_value_amount, traced_value_asset, tracing_method (proportional|fifo|none), value_continuity_ratio, relevance_criteria jsonb, has_break, break_reason, edges jsonb (full P6 fields).
- case_attributions: case_id, path_id, label_id, connection_type, attribution_state, attribution_confidence_level (high|medium|low|none), confidence_factors jsonb, label_is_stale, shared_infrastructure_flag, explanation.
- case_signals: case_id, path_id nullable, signal_key, level, evidence_tag, feature_values jsonb, explanation, limitation_note.
- case_links: case_a_id < case_b_id, strength, evidence_tag, shared_addresses, shared_transactions, shared_path_segments, shared_infrastructure_flag, temporal_notes, first_observed_at, last_updated_at, change_history. Unique (case_a_id, case_b_id).
- audit_events: case_id nullable, event_type (case_created, retrieval_started, retrieval_completed, retrieval_failed, graph_built, attribution_applied, signals_computed, corroboration_run, report_generated, case_deleted), occurred_at, actor, sanitized payload, payload_hash (SHA-256, chained).
- reports: case_id, generated_at, file_hash_sha256, storage_reference, retention_until.
- Seed command refuses level_0_synthetic entries unless DEMO_MODE is true.

## API (base /api/v1, JSON, snake_case, ISO 8601 UTC, request_id header, uniform ErrorResponse)
- Error codes: invalid_address, invalid_chain, invalid_tx_hash, invalid_date, limit_exceeded, rate_limited, upstream_unavailable, upstream_timeout, case_not_found, report_not_ready, internal_error. Error body: error{code, message, field?, request_id}.
- POST /cases (202, background analysis, sync allowed in test mode; 422 with field and code). Input models forbid extra fields. Fields: address (1-128 chars, validated per chain), chain, tx_hash, incident_date (not future), incident_date_precision, reported_amount (non-negative), reported_asset, parameters override (max_hops, time_window_days, max_nodes, max_edges within hard limits), narrative (max 4000) with consent_for_narrative_storage required when present.
- GET /cases/{ref} (CaseSummaryResponse with progress stages: retrieval, graph, attribution, behavior, corroboration, assembly; headline_state, summary_text from copy deck, confidence_panel with four independent entries, limitations, demo_notice).
- GET /cases/{ref}/paths (paginated PathResponse with itemized relevance_criteria), /attributions, /signals, /related.
- POST /cases/{ref}/refresh (stricter rate limit, records what changed).
- GET /cases/{ref}/report.pdf (409 report_not_ready if incomplete).
- GET /cases/{ref}/audit (investigator role; returns integrity verification).
- GET /labels/{chain}/{address} (labels with provenance or explicit "no match in current references").
- GET /health and /health/ready.
- Every claim-bearing object has evidence_tag. Idempotent create within a short window. Security headers on all responses. OpenAPI descriptions and examples on every model.

## Adapter layer
- Abstract `ChainDataAdapter`: validate_address, get_native_transfers, get_internal_transfers, get_token_transfers, get_transaction, block_for_timestamp, describe. Returns `AdapterResult{items, source_name, retrieved_at, request_count, truncated, warnings, errors}` of `NormalizedTransfer`.
- Addresses canonical (EIP-55) at the boundary. Amounts are integers in smallest unit; decimal amount derived, null plus warning if decimals unknown. Failed txs kept but excluded from value tracing. Contract creation and self-transfers flagged.
- Etherscan adapter: token-bucket rate limit, full pagination up to a configurable cap (default 10000 per address) then `truncated=true` with warning (never silently drop), exponential backoff with jitter on timeout/5xx/429 only, "No transactions found" is an empty success, map upstream errors to typed exceptions without leaking keys or URLs, audit every upstream call with sanitized descriptor.
- Cache keyed by adapter, method, normalized params. Long TTL only when the block range is below head minus 64 blocks. Store retrieved_at. Provide bypass for evaluation.
- Mock adapter: deterministic JSON fixtures in `backend/data/fixtures`, no network, source "mock_fixture", triggers demo notice. RPC adapter is a documented stub.
- Document known gaps in `docs/limitations.md`: internal transfer coverage, non-standard token events, swaps change asset identity (break `swap_asset_change` unless decoded), data near chain head may reorganize.

## Graph engine
- NetworkX MultiDiGraph; nodes are canonical addresses (first_seen, last_seen, observed degrees, is_contract, is_hub, label_ids); edges keyed by (tx_hash, log_index).
- Expansion: seed from tx hash (anchored) or reported address with a time window centered on incident date (else most recent window). BFS by hop to max_hops. Window for hop n starts at arrival time of traced value. Enforce node and edge budgets and a 90 s wall-clock deadline; on hit, stop, record `expansion_limit_reached` or `data_unavailable`, set partial. Do not expand hubs (degree above threshold) or active labelled exchange, hot wallet, deposit address, mixer, bridge or DEX nodes; keep them as terminal nodes (where attribution applies). Optional incoming expansion of one hop (default off). Deduplicate. Persist retained transfers.
- Paths: time-respecting simple paths (timestamps non-decreasing, within per-hop window), prune continuity below 0.05, cap at 25 and report omitted count.
- Value tracing, per asset, both `proportional` and `fifo` behind one interface. Asset change ends tracing with `swap_asset_change`. Gas is not counted as traceability loss. Output traced value and continuity ratio tagged derived. Every report states that the method estimates value movement and does not prove specific units moved.
- Breaks: mixer/bridge labels, maintained sourced list of privacy-protocol contracts, non-transfer unlabelled contract interactions, asset changes.
- Ranking: transparent ordered criteria, no hidden score, weights in config, every criterion stored and shown: anchored to reported tx, continuity ratio, time proximity of first edge to incident, fewer hops, terminal labelled. Ranking orders display only.
- Pattern detection (derived, with supporting tx refs): splitting (out-degree 3 or more in interval), merging (in-degree 3 or more), rapid pass-through, repeated equal-value transfers, peel-chain shape.
- Targets: under 20 s on mock, under 60 s live, bounded-semaphore asyncio.

## Attribution
- Registry seeded from `backend/data/label_registry/*.json`. Only publicly citable addresses with URL and date; otherwise omit. A few clearly marked level_0_synthetic entries for demo. Admin CLI to add, update, deactivate labels; every change goes to label_change_log.
- Matching: exact canonical address and chain. direct = first receiver of the seed transfer; indirect = after intermediaries; inferred only from inferred_cluster labels. Path ending at unlabelled address gives `no_match_in_current_references`; truncated or broken path gives `insufficient_data`.
- Confidence (no probability, explicit rule table, return all factors): high = level_3 or 2+ independent level_2 sources, observed_label, not stale, direct or indirect, path intact. medium = single level_2, or level_3 but stale, observed_label, path intact. low = level_1 only, inferred_cluster, stale single source, or path with break. none = no label, or synthetic outside demo. verified_label_match requires high or medium with observed_label and non-synthetic; potential_association covers low or inferred.
- Factors: verification level, label origin, staleness, scope match, independent source count, connection type, path integrity.
- Shared-infrastructure list with sources; sets `shared_infrastructure_flag`.
- Explanation text from templates naming source, connection type, verification level, staleness or scope caveats. Never imply exchange knowledge or involvement.

## Behavioral signals
- Features: temporal (receipt-to-onward seconds median and min, burst count, activity within 24 h of incident), structural (degrees, split and merge factors, depth, branching), value movement (distinct and repeated amounts, onward-to-received ratio, asset changes, round-number share), counterparty (distinct counts, labelled types, hub interactions), case context (incident-to-first-transfer offset, proximity to reported tx, reported vs traced ratio).
- Rule signals: rapid_pass_through, fan_out_splitting, fan_in_merging, peel_chain_pattern, equal_value_repetition, new_address_chain, asset_hopping. Thresholds in config with rationale.
- ML baseline: logistic regression and gradient boosting on a documented dataset (public research data checked for task fit, or clearly marked synthetic), features limited to the families above, no identifiers or leakage, time-based splits, model card at `backend/data/models/model_card.md`. Expose calibrated output only if calibration is evaluated; otherwise coarse pattern-similarity level, never a percentage. If no model is present, run rules only and say so in limitations.
- Every signal carries the fixed note "This pattern can also result from legitimate activity."

## Corroboration
- Compare a case against other cases on the same chain: shared path-node addresses (excluding either reported address unless downstream in the other), shared tx hashes, overlapping consecutive segments, similar temporal structure (inferred, weak only).
- Exclude shared-infrastructure labelled nodes and nodes above CORROBORATION_HUB_EXCLUSION_DEGREE; if only those overlap, strength is weak with the flag. Require time skew within CORROBORATION_MAX_TIME_SKEW_DAYS. Strengths per vocabulary above.
- Temporal updating: re-run on new data, keep first_observed_at, append change_history with the new evidence. Manual refresh endpoint rate limited.
- Privacy: show only case references and shared chain evidence, never another reporter's narrative, contact or amount. Related cases visible only with sharing consent; otherwise return an aggregate count with shared evidence and no reference.

## Evidence assembly
- CaseEvidencePackage: inputs, parameters, sources, retrieval times, snapshot id, ranked paths, attributions, signals, related cases, limitations, four-entry confidence panel, summary text, versions (code, model, label registry snapshot hash).
- Headline precedence: (1) retrieval failed entirely gives status failed; (2) no transfers in window gives no_paths_found; (3) any verified_label_match; (4) any potential_association; (5) any truncated or broken path gives insufficient_data; (6) otherwise no_match_in_current_references.
- Limitations generator always includes applicable adapter gaps, truncation, breaks, label staleness and scope, demo notice, unsupported chain or asset, partial analysis, analysis timestamp, and the standing statement.
- Audit: one event per stage, sanitized payload, SHA-256 hash chain, verification function. No secrets or narrative in payloads.

## PDF report (ReportLab, A4 portrait, 20 mm margins, one sans family, monospace for addresses and hashes, no color-coded verdicts, neutral header and footer with case reference, page numbers, analysis timestamp)
Sections in order: 1 cover block; 2 statement of use and evidence tag definitions; 3 summary; 4 confidence panel; 5 inputs and parameters; 6 data sources; 7 fund movement (edge table per path); 8 potential exchange or service links with provenance; 9 behavioral signals; 10 related reports; 11 limitations; 12 audit summary (events, hashes, versions, registry hash); 13 glossary. SHA-256 of the file stored in `reports` and printed in the last page footer. Long hashes wrap, never truncate.

## Frontend
- Routes: `/` HomePage, `/cases/:caseReference` ResultPage, `*` NotFoundPage.
- HomePage order: product name and one-line description, form, short note on what the tool does and does not establish, link to limitations. Form: address (required, monospace, trim, format check on blur), chain selector (single option), "Additional details" disclosure (tx hash, incident date with precision, reported amount and asset), primary button "Check Wallet" (disabled while submitting, shows progress text). No narrative field on the public form.
- ResultPage: top bar (case reference, chain, timestamp, export, new check), then bordered panels in order: Summary (neutral status badge, demo notice), Confidence panel (four text rows, no numbers, no progress bars), Fund movement (ranked path rows; selecting opens graph plus edge table), Potential exchange link, Why it was flagged (signals with limitation note), Related reports, Limitations with standing statement, Export (PDF and copy reference).
- Components: form (AddressInput, OptionalDetails, SubmitButton); result (SummaryPanel, ConfidencePanel, StatusBadge, LimitationsList, DemoNotice); evidence (PathList, PathRow, EdgeTable, AttributionCard, LabelProvenanceTable, SignalList, RelatedCaseCard, EvidenceTagLabel); graph (PathGraph in React Flow, left to right, address chips, edges labelled with date and amount, labelled terminals outlined, break markers with reason); feedback (ProgressStages, ErrorPanel, EmptyState, PartialDataNotice, SkeletonBlock); common (MonoText, CopyButton, ExpandablePanel, ExternalLink, Timestamp).
- States, each implemented and tested: initial/validating, submitting, running with named stages, completed, completed with no paths, completed with insufficient data, partial, failed with retry, rate limited with retry-after text, not found, offline or upstream unavailable.
- Behavior: polling with backoff, deep links survive reload, copy control on every address and hash (text confirmation, no icon animation), addresses shown as first 6 and last 4 with full value on expand or tooltip and in edge tables, UTC times with optional local time, explorer links in new tab with rel noopener noreferrer.
- Accessibility: WCAG 2.1 AA, landmarks, one h1 per page, keyboard access and focus ring, form errors via aria-describedby and aria-live polite, table alternative always available for the graph, color never sole meaning, respect prefers-reduced-motion.
- Visual design: institutional, restrained, document-like, like a government or research portal. Prohibited: emojis, decorative icons, gradients, glassmorphism, glow, neon, hacker themes, animated backgrounds, red and green guilt verdicts, traffic-light meters, skull or siren imagery, stock or 3D coin illustrations. Lucide icons only for copy, external link, expand and collapse, download, close (16 or 20 px, stroke 1.5).
- Tokens (`tokens.css`, light theme): background #F7F8FA, surface #FFFFFF, surface-subtle #F1F3F6, border #D9DEE5, border-strong #B8C0CC, text-primary #1B2430, text-secondary #4A5565, text-muted #6B7686, accent #2F5D8A, accent-hover #264C72, accent-subtle #E6EEF6, status-neutral #4A5565 on #EDEFF3, status-attention #7A5A12 on #F6EFD9, status-info #2F5D8A on #E6EEF6, focus ring 2px offset 2px. Verify WCAG AA contrast and adjust failing pairs. Provide a dark theme via prefers-color-scheme.
- Type and shape: Inter or IBM Plex Sans; IBM Plex Mono or JetBrains Mono only for addresses, hashes, case references; scale 12/14/16/18/20/24/30 px, body 16 px at line height 1.5, headings weight 600; tabular figures; 4 px base spacing; radius 4 px controls and 6 px panels; 1 px borders; max width 960 px; 32 px between panels; mobile first from 360 px with graph collapsing to table.
- Buttons: primary solid accent, secondary outlined, minimum 40 px height, no icon-only primary actions. Panels: white, 1 px border, 24 px padding. Evidence tags: text-only "Observed", "Derived", "Inferred" with tooltip definitions.

## Copy deck (`docs/copy-deck.md` and `frontend/src/lib/copy.ts`; all UI strings come from copy.ts)
- Approved phrases: "Potential exchange connection identified", "Verified label match", "Potential association", "No match found in current references", "Insufficient data", "No fund movement found for this address in the selected window", "Observed transfer", "Label source", "Pattern observed".
- Prohibited phrases (add a lint test scanning copy.ts, templates and docs; keep the list in a lint config file that the scan excludes): criminal exchange, fraudulent exchange, scam wallet confirmed, guilty, proof of fraud, fraud score, risk percentage, definitely, confirmed scammer, the exchange is responsible, and any statement of intent or knowledge attributed to an exchange or wallet owner.
- Templates:
  - potential_association: "We checked address {address} on {chain} using data retrieved on {date}. Funds sent from this address appear to have moved through {hop_count} transfer(s) to an address labelled {entity} by {label_source}. This is a potential connection based on observed transfers and a label of {verification_level} verification. It does not show that the service knew of or took part in any wrongdoing."
  - verified_label_match: "We checked address {address} on {chain} using data retrieved on {date}. An observed transfer path reaches an address labelled {entity} in a source with {verification_level} verification. This describes where funds moved. It does not establish involvement or intent by the service."
  - no_match_in_current_references: "We checked address {address} on {chain} using data retrieved on {date}. We traced observed transfers within the selected limits and did not reach an address present in our current label references. This does not rule out a connection to a service that is not in our references."
  - insufficient_data: "We could not reach a conclusion for address {address} on {chain}. {reason}. Please review the limitations section."
  - no_paths_found: "No outgoing transfers were found for address {address} on {chain} in the selected time window."
  - Related report caution (mandatory): "These cases share the on-chain evidence shown below. Shared addresses can result from common services, exchange deposit infrastructure, or coincidence, and do not by themselves indicate common ownership or coordination."
  - Signal note (mandatory): "This pattern can also result from legitimate activity."
  - Standing statement (result page and report): "This output is an investigative lead for human review. It is not a legal finding and does not accuse any person or organization."
  - Demo notice: "Demonstration mode. This result uses simulated data or synthetic labels and does not describe a real investigation."

## Security and privacy
- Validate and canonicalize every address, hash and date server side; enforce body and field limits; render user text as escaped text only.
- Secrets only in env or a secret manager; pre-commit secret scan; frontend never calls the explorer or receives keys.
- HTTPS in production; HSTS, CSP, X-Content-Type-Options, Referrer-Policy no-referrer, X-Frame-Options deny; CORS allowlist.
- Per-IP rate limits with Retry-After, cap on concurrent analyses with a bounded queue and a clear busy response, request timeouts, cancel abandoned analyses.
- Public: create case, read own case by unguessable reference, label lookup, health. Roles: investigator (audit, consented private details) and administrator (label management) via simple token scheme; document the production identity plan.
- No public accounts. Retention job deletes expired cases, private details and reports and writes case_deleted audit events. Never link addresses to personal identities. Logs exclude narrative and contact; addresses only at debug level in development.
- Pin dependencies, run pip-audit and npm audit in CI (fail on high), minimal non-root container images.

## Observability
Structured JSON logs with request_id, case_reference, stage, duration_ms, outcome. Counters for cases created, cases by headline state, upstream calls, cache hits, failures; latency histograms; one correlation id from request through background analysis to audit events.

## Testing
- Unit: address validation (valid, bad checksum, wrong length, wrong chain, mixed case, whitespace), adapter normalization with respx (decimals, failed txs, pagination, truncation, empty, error mapping), graph (seeds, time order, budgets, hubs, terminals, dedupe), value tracing (hand-computed examples), attribution (every state, every confidence rule, staleness, scope, synthetic in and out of demo), behavior rules (positive and negative fixtures, threshold boundaries), corroboration (strong, moderate, weak, none, infrastructure exclusion, skew, privacy), evidence (headline precedence, limitations, audit chain), reports (sections, hash, wrapping).
- Property (hypothesis): no decreasing timestamps, budgets never exceeded, traced value never exceeds originating value, identical output on repeat runs.
- Integration: full case to report on mock adapter for every fixture; upstream timeout gives partial or failed with limitation; 429 with Retry-After; retention deletes.
- Frontend: a test per state, form validation, copy lint, axe on Home and Result, one Playwright run (enter demo address, view result, expand evidence, download report).
- Fixtures (`backend/data/fixtures`): 1 direct_exchange_deposit; 2 multi_hop_indirect (three intermediaries); 3 split_and_merge; 4 mixer_break (mixer_interaction plus insufficient_data); 5 bridge_break; 6 swap_asset_change; 7 unlabelled_destination; 8 stale_label; 9 shared_infrastructure_overlap (weak with flag); 10 strong_corroboration (two-edge shared segment); 11 truncated_history; 12 no_outgoing_transfers; 13 malformed_input_set; 14 upstream_failure.

## Evaluation (`make eval`, code in `backend/app/evaluation`, docs in `docs/evaluation.md`, results as machine-readable files under `docs/evaluation/results`)
- Data: public labelled research data only where chain and task match (state version, license, class balance, label semantics); a synthetic case generator with controllable noise (missing hash, approximate date, wrong amount) marked synthetic; a curated label set for attribution tests.
- Experiments: wallet behavior (rules vs standard ML vs interpretable model; precision, recall, F1, PR-AUC, FPR); path relevance (unfiltered vs report-conditioned; relevant at k, irrelevant volume, runtime); attribution (single-label lookup vs provenance-aware; accuracy, calibration error where applicable, abstention rate); corroboration (independent vs cross-report; pairwise precision and recall, false associations including infrastructure traps, traceability rate); temporal robustness (random vs time split); noisy inputs; usability with 5 to 10 participants with consent and anonymization.
- Ablations: remove report conditioning, remove provenance and confidence, disable corroboration, remove temporal features.
- Rigor: time-based splits, leakage prevention across graph neighborhoods, fixed seed, recorded library versions, report failures too, never present research-dataset results as real-world victim-report performance. Also report latency percentiles, evidence completeness, upstream calls per analysis, correct abstention rate. Output ends with an honest limitations paragraph.

## Claims to avoid (code comments, docs, UI, README, slides)
Detection of every fraudulent exchange; any claim that a transfer to an exchange proves involvement; definitive fraud verdicts or AI-determined guilt; that no existing platform does graph tracing or attribution; high accuracy before metrics are measured; complete traceability across mixers, bridges or privacy systems. Also out of scope: naming any person or exchange as criminal from model output; replacing law enforcement, compliance or legal process.

Novelty statement (use exactly): "The contribution is an integrated, victim-report-conditioned, uncertainty-aware investigation workflow combining case-focused tracing, provenance-aware exchange attribution, and cross-report corroboration in one explainable output. Novelty is a hypothesis to be validated by literature review, baseline comparison, and ablation."

## CI and repo checks
Docker compose runs db, api, frontend with hot reload, demo mode and mock adapter by default. CI stages: install, lint, type check, backend tests with coverage, frontend tests, build, dependency audit, copy lint, secret scan, and a scan that fails on non-ASCII pictographic characters anywhere in the repo. README contains overview, safety and limitations summary, quick start, configuration table, how to test and evaluate, structure, contribution notes, and the claims-to-avoid list.
