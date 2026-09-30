# TRACE-X

Trust-aware Risk Analysis and Connection Evidence for Cryptocurrency Exchanges

## Overview

TRACE-X is an investigative analysis system designed to identify cryptocurrency exchanges and custodial services potentially connected to reported fraud. Starting from suspect wallet addresses reported by victims, the system reconstructs fund movements, correlates destination endpoints with verified entity labels, assesses behavioral patterns, and corroborates overlapping paths across incident reports.

Novelty statement: The contribution is an integrated, victim-report-conditioned, uncertainty-aware investigation workflow combining case-focused tracing, provenance-aware exchange attribution, and cross-report corroboration in one explainable output. Novelty is a hypothesis to be validated by literature review, baseline comparison, and ablation.

## Safety and limitations summary

- Standing statement: This output is an investigative lead for human review. It is not a legal finding and does not accuse any person or organization.
- Attribution distinction: An observed transfer to an exchange deposit address indicates where funds moved. It does not establish complicity, knowledge, or intent on the part of the receiving service.
- Evidence tagging: Every data point carries an evidence tag indicating whether it is observed (raw chain event), derived (deterministic calculation), or inferred (heuristic or statistical model).
- Abstention: When data is missing, truncated, or obfuscated by mixers or privacy contracts, the system records explicit abstention states rather than guessing.

## Claims to avoid

The following claims are strictly out of scope and prohibited across all documentation, code comments, and interfaces:
1. Detection of every fraudulent exchange.
2. Any claim that a transfer to an exchange proves involvement.
3. Definitive fraud verdicts or automated guilt determinations.
4. Claims that no existing platform performs graph tracing or attribution.
5. High accuracy claims prior to standardized benchmark evaluation.
6. Claims of complete traceability across mixers, cross-chain bridges, or privacy networks.
7. Designating any person or organization as criminal based on algorithmic output.
8. Replacing law enforcement investigations, compliance obligations, or formal legal processes.

## Quick start

### Prerequisites
- Docker and Docker Compose, or
- Python 3.11+ and Node.js 18+

### Running with Docker Compose
```bash
docker-compose up --build
```
The application will be available at:
- Web interface: http://localhost:5173
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

### Local development setup
```bash
make setup
make dev
```

## Configuration parameters

| Parameter | Default | Description |
|---|---|---|
| APP_ENV | development | Application runtime mode (development, test, production) |
| DEMO_MODE | true | Enables synthetic fixture execution and sample data |
| DATA_ADAPTER | mock | Data retrieval adapter (mock, etherscan, rpc) |
| CHAIN_DEFAULT | ethereum | Primary blockchain network |
| GRAPH_MAX_HOPS_DEFAULT | 4 | Default forward traversal depth (hard limit: 6) |
| GRAPH_MAX_NODES_DEFAULT | 500 | Node expansion limit per analysis (hard limit: 2000) |
| GRAPH_MAX_EDGES_DEFAULT | 2000 | Edge expansion limit per analysis (hard limit: 8000) |
| GRAPH_HIGH_DEGREE_THRESHOLD | 200 | Degree cutoff for hub non-expansion |
| LABEL_STALE_AFTER_DAYS | 365 | Threshold after which entity labels are marked stale |
| ALLOW_SYNTHETIC_LABELS | false | Permit level 0 synthetic labels (only valid when DEMO_MODE is true) |
| RATE_LIMIT_CASES_PER_MINUTE_PER_IP | 10 | Case creation rate limit |

## Testing and evaluation

Run the verification test suite:
```bash
make test
```

Execute static typing and linting checks:
```bash
make lint
make typecheck
```

Execute the evaluation benchmark suite:
```bash
make eval
```

## Repository structure

```
trace-x/
  docs/                  Methodology, architecture, and regulatory documentation
  backend/               FastAPI service, graph engine, and adapters
    app/core/            Configuration, logging, security, and constants
    app/adapters/        Blockchain data providers (Etherscan, RPC, Mock)
    app/api/             REST API endpoints and serialization schemas
    app/graph/           Network expansion and value tracing algorithms
    app/attribution/     Entity label matcher and confidence scoring
    app/behavior/        Structural and temporal feature extraction
    app/corroboration/   Cross-case overlap matching
    app/evidence/        Evidence package assembly and cryptographic audit log
    app/reports/         PDF evidence dossier generation
  frontend/              React 18, Vite, and Tailwind web interface
```

## Contribution notes

All code, tests, documentation, and commit messages must conform to the project guidelines:
- English in sentence case with neutral, objective terminology.
- No emojis or decorative symbols.
- Strict type checking on both backend (mypy strict) and frontend (TypeScript strict).
- Explicit evidence tags on all analytical outputs.
