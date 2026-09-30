# Attribution methodology

## Overview
Attribution correlates terminal path addresses with known entity labels in the reference registry. The engine evaluates source provenance, verification levels, connection topology, and data freshness to derive an attribution state and confidence rating without subjective scoring.

## Attribution states
- `verified_label_match`: High or medium confidence match backed by primary or secondary reputable sources on an intact path.
- `potential_association`: Lower confidence match, inferred cluster association, or path with break points.
- `no_match_in_current_references`: Path terminates at an unlabelled address present in chain data but absent from the reference registry.
- `insufficient_data`: Expansion was truncated, or transfers entered an opaque smart contract, mixer, or unsupported protocol.

## Confidence determination
Confidence is determined by rule evaluation across seven explicit factors:
1. Verification level of source (`level_3_primary_source`, `level_2_reputable_secondary`, `level_1_community_or_unverified`, `level_0_synthetic`).
2. Label origin (`observed_label` vs `inferred_cluster`).
3. Label freshness (staleness threshold: 365 days).
4. Scope alignment (e.g. deposit address vs hot wallet).
5. Number of independent corroborating sources.
6. Connection type (`direct` vs `indirect`).
7. Path integrity (whether breaks or truncation occurred).

## Shared infrastructure handling
Deposit addresses, smart contract forwarders, multi-tenant settlement routers, and bridge gateways are flagged with `shared_infrastructure_flag`. These nodes never imply common ownership or control between distinct interacting counterparties.
