# Cross-report corroboration methodology

## Purpose
Victim reports submitted independently may share destination paths, intermediary consolidation addresses, or cash-out deposit accounts. Corroboration detects overlapping subgraphs across distinct cases while enforcing strict privacy isolation.

## Overlap matching criteria
Two cases are matched for potential correlation based on:
1. Shared non-infrastructure path addresses.
2. Shared transaction hashes.
3. Identical consecutive path segments (length 2 or greater).
4. Temporal alignment within `CORROBORATION_MAX_TIME_SKEW_DAYS` (default 45 days).

## Strength classification
- `none`: No overlapping nodes or segments.
- `weak`: Single shared high-degree or shared infrastructure address.
- `moderate`: Shared non-infrastructure address or single-hop segment overlap.
- `strong`: Two or more consecutive shared path edges with consistent chronological order, excluding shared infrastructure.

## Privacy protections
1. No narrative or personal contact information is shared between cases.
2. If explicit consent for cross-case sharing is not granted, only an aggregate count of related cases with shared chain artifacts is displayed.
3. Mandatory caution notice:
"These cases share the on-chain evidence shown below. Shared addresses can result from common services, exchange deposit infrastructure, or coincidence, and do not by themselves indicate common ownership or coordination."
