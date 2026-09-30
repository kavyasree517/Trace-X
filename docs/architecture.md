# Architecture specification

## System overview
TRACE-X is organized into decoupled layers:
1. Data ingestion layer: Abstracts blockchain access through a unified adapter interface (`ChainDataAdapter`), supporting Etherscan, RPC nodes, and deterministic mock fixtures.
2. Graph analytics engine: Builds directed multigraphs with NetworkX, enforces expansion budgets, identifies structural breaks, and computes value tracing using proportional and FIFO models.
3. Attribution engine: Matches terminal addresses against a provenance-aware entity registry and computes multi-factor confidence ratings.
4. Behavioral analysis engine: Extracts temporal, structural, and counterparty features to detect flow patterns.
5. Corroboration engine: Evaluates cross-case subgraph overlap to detect shared infrastructure and multi-victim patterns.
6. Evidence assembly and reporting: Compiles unified case evidence packages, maintains an immutable SHA-256 audit hash chain, and renders forensic PDF dossiers using ReportLab.
7. Frontend user interface: Single-page React application providing structured form entry, interactive path inspection, React Flow topology visualization, and tabular evidence verification.

## Component diagram
```
[User Interface] <-> [FastAPI Application]
                           |
            +--------------+--------------+
            |                             |
      [Graph Engine]             [Data Adapters]
            |                             |
    +-------+-------+             +-------+-------+
    |               |             |       |       |
[Attribution]  [Behavior]       [Mock] [Ether]  [RPC]
    |               |
[Corroboration] [Audit]
            |
    [Evidence Assembly]
            |
    [ReportLab PDF / DB]
```
