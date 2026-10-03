# TRACE-X continuation notes

Read this file first, then continue from the marked point. The governing
specification is `AGENTS.md` (identical to `.agent/rules/trace-x.md`). The
team's original `TRACE-X_Master_Prompt.pdf` cannot be read directly by the
model, so `AGENTS.md` is treated as the master prompt.

## How to resume

Working directory: `C:\Users\suved\Downloads\Trace-X`
Say "continue" and work through the phases below in order, running the
verification commands after each one.

## Environment

- Backend virtualenv already created at `backend/.venv` (Python 3.12).
- Reinstall after dependency changes with:
  `cd backend; .\.venv\Scripts\python.exe -m pip install -e ".[dev]"`
- Verification commands (run from `backend`):
  - `.\.venv\Scripts\python.exe -m pytest tests/ -q`
  - `.\.venv\Scripts\python.exe -m ruff check app/ tests/`
  - `.\.venv\Scripts\python.exe -m mypy app`

## CURRENT STATE: all checks green

Run from `backend`:
- pytest: 186 passed
- ruff format: 63 files already formatted
- ruff check: all checks passed
- mypy strict: no issues in 54 source files
- app coverage: 88 percent

Run from the repo root:
- `python scripts/lint_copy.py`: passed
- `python scripts/check_characters.py`: passed
- `python scripts/check_secrets.py`: passed

## What the team had already built (do not redo)

- Repo layout, all 14 docs, CI, Makefile, docker-compose, scripts, README
- `app/core/`: config, constants, enums, logging, rate_limit, security, time
- `app/models/`: all 8 SQLAlchemy models
- `app/schemas/`: all 9 schema modules
- `app/adapters/`: base, mock, etherscan (stub), registry, cache, rpc_stub
- `app/api/`: errors, deps, health, labels (stub), cases (stub), router
- `app/main.py`, `alembic/` scaffolding
- Fixtures 01 and 12 only

## Work completed in this session

### Phase 0: foundation fixes (DONE)
- `backend/pyproject.toml`: `readme` pointed outside the build root and broke
  `pip install`; changed to `backend/README.md` and created that file.
- `pyproject.toml`: added `eth-hash[pycryptodome]` (eth_utils had no backend).
- `pyproject.toml`: ruff ignores `UP042` (str+Enum kept for Pydantic v2).
- `pyproject.toml`: mypy `explicit_package_bases`, `namespace_packages`,
  `mypy_path = "typings"`, override for `deprecated.*`.
- Created `backend/typings/networkx/__init__.pyi` so mypy strict can verify
  graph code (NetworkX ships no types).
- `app/core/security.py`: import from `eth_utils.address` submodule.
- `app/core/logging.py`: typed the structlog processor, return type fixes.
- `app/adapters/base.py`: `AdapterResult.retrieved_at` used naive
  `datetime.utcnow`; changed to timezone-aware UTC. Added `edge_key` and
  `is_success` helpers.
- `app/api/v1/health.py`: `raise ... from exc` (B904).
- `app/core/config.py`: added the missing spec keys (graph budgets, deadline,
  path caps, ranking weights, behaviour rule thresholds, rate limits,
  concurrency, idempotency window, retention, adapter caps).
- Ran `ruff format` over `app/models` and `app/schemas`.

### Phase 1: graph engine (DONE, tested)
Files created:
- `app/graph/__init__.py`
- `app/graph/builder.py` - TraceGraph (MultiDiGraph), node/edge metadata,
  dedupe, `iter_edge_transfers`, `all_successful_transfers`, `node_degree`
- `app/graph/value_tracing.py` - proportional and fifo methods behind
  `trace_value`
- `app/graph/breaks.py` - mixer, bridge, privacy, unsupported contract,
  asset change
- `app/graph/expansion.py` - BFS with hop/node/edge/wall-clock budgets,
  terminal nodes for hubs and labelled services
- `app/graph/paths.py` - time-respecting simple paths, continuity pruning,
  cap with omitted count, `PathEdgeRecord` holding the full P6 field set
- `app/graph/ranking.py` - ordered criteria with weights in config, full
  breakdown returned, no probability language
- `tests/conftest.py`, `tests/unit/test_graph.py` (31 tests including
  hypothesis property tests)

Important design notes for the next phase:
- `enumerate_paths` needs an `onward_pool` of all known transfers so a split
  is attributed proportionally. `_build_candidate` receives it.
- Value tracing takes `onward_pool` as an optional third argument. Without it
  the path edges are used, which overstates the traced amount.
- Two engine bugs were found and fixed by the tests: `get_edge_data` returns
  `{key: attrs}` (one level, not nested) and `out_edges(keys=True, data=True)`
  returns 4-tuples, not 3. Edge traversal is now centralised in
  `builder.iter_edge_transfers`.

### Phase 2: attribution (DONE, tested)
Files created:
- `app/attribution/confidence.py` - rule table returning a level plus all
  factors, never a probability. States include `INSUFFICIENT_DATA` for
  broken paths, `NO_MATCH_IN_CURRENT_REFERENCES` for unlabelled terminals.
- `app/attribution/registry.py` - JSON loading with strict validation
  (citable URL required, `last_verified_at` required for non-synthetic,
  synthetic refs must be under `example.invalid`), snapshot hash
- `app/attribution/matcher.py` - direct/indirect classification, per-label
  matching, neutral explanation text using a `_STATE_SENTENCE` mapping
- `app/attribution/infrastructure.py` - shared-infrastructure assessment and
  exclusion for corroboration
- `app/attribution/seed.py` - admin CLI (`sync`, `add`, `update`,
  `deactivate`) with `--dry-run`, change planning and `label_change_log`
  writes for created, updated and deactivated
- `app/attribution/__init__.py` - public exports
- `data/label_registry/entities.json` - registry with real citable entries
  (Binance, Circle, Tether, Uniswap, Starknet bridge) and clearly marked
  synthetic demo entries
- `tests/unit/test_attribution.py`, `tests/unit/test_seed_cli.py`

Synthetic handling is verified working: `load_registry` with `is_demo=True`
loads 10 labels, with `is_demo=False` loads only the 5 citable real labels and
skips the 5 synthetic ones with a warning.

Phase 2 follow-up work completed in this session:
1. The "Tornado Cash" entry that failed EIP-55 validation and had no public
   source was deleted rather than corrected, recorded as `DEC-004`. The
   registry now loads 10 demo labels with 0 errors.
2. `tests/conftest.py` pointed at the wrong registry directory
   (`parents[2]` instead of `parents[1]`); fixed.
3. Confidence fixes found by the new tests: synthetic demo labels now return
   `low` with a `synthetic_demo_only` factor, and `none` maps to
   `no_match_in_current_references` rather than a potential association.
4. `pyproject.toml` now depends on `sqlalchemy[asyncio]` so aiosqlite works
   under greenlet.

## CORRECTION: phase numbering now matches the master prompt

Earlier notes in this file used a locally invented numbering
("Phase 0", "Phase 1: graph engine", "Phase 2: attribution"). That was a
mistake. The master prompt defines its own eight phases in Part 26, and
every acceptance criterion is written against those. Earlier work is
credited below under the master prompt numbering.

The master prompt PDF is now readable text at `docs/master-prompt.md`
(extracted with pypdf and normalised to ASCII). Use it as the authority
whenever `AGENTS.md` is ambiguous. Where the two differ, the PDF wins.

## Status against the master prompt phases

- **Phase 1, scaffold and foundations: substantially done.** Layout,
  config loader, logging, error model, health endpoints, Docker, Makefile,
  CI, mock adapter, fixtures 01 and 12, copy and character and secret lint
  all exist and pass. Missing: the frontend shell with design tokens, which
  is why the frontend has no `src` directory at all.
- **Phase 2, validation, retrieval, storage, basic result page: the first
  incomplete phase and the current work.** Done: all 8 SQLAlchemy models,
  the mock adapter, 2 fixtures. Missing and blocking: no Alembic migration
  exists (`alembic/versions/` is empty), `app/adapters/etherscan.py` is a
  stub with 5 `NotImplementedError` calls, `app/api/v1/cases.py` is a
  6-line stub, and there is no HomePage or ResultPage.
- **Phase 3, graph tracing: engine done, delivery not.** `app/graph/` is
  complete and tested (builder, expansion, paths, value tracing, breaks,
  ranking). Missing: pattern detection, the path API, PathList and PathGraph
  with a table alternative, and fixtures 02 to 06 and 11.
- **Phase 4, attribution and provenance: backend done, delivery not.**
  `app/attribution/` is complete and tested, including the admin CLI and
  change log. Missing: the attribution API endpoint, the UI attribution card
  with a provenance table, and fixtures 07 and 08.
- **Phase 5, behavioral signals: not started.** `app/behavior/` holds an
  empty `__init__.py` only.
- **Phase 6, cross-report corroboration: not started.**
  `app/corroboration/` holds an empty `__init__.py` only.
- **Phase 7, evidence, audit, report, polish: not started.**
  `app/evidence/` is empty and `app/reports/` does not exist.
- **Phase 8, evaluation, documentation, demo: not started.**
  `app/evaluation/` is empty. The 14 docs exist but several predate the
  implementation and describe intended rather than actual behaviour.

Roughly a third of the project is done. The remaining work is dominated by
the frontend, which has not been started.

## Next work: master prompt Phase 2

Build in this order, because each step unblocks the next:

1. Alembic migration covering all 8 models with a working downgrade. Nothing
   can persist until this exists, so every later phase depends on it.
2. Address, transaction hash and date validation, then `POST /cases` and
   `GET /cases/{case_reference}` per Part 17.1 and 17.2, with the error
   codes in Part 9.
3. Replace the Etherscan stub with a real adapter per Part 10: token bucket
   rate limit, pagination to a configurable cap with `truncated=true`, retry
   with jitter on timeout and 5xx and 429 only, "No transactions found" as an
   empty success, and typed error mapping that never leaks the API key.
4. The frontend shell with `tokens.css` and a contrast-checked sample page
   to close out Phase 1.

Design notes carried forward from the graph engine:
- `enumerate_paths` needs an `onward_pool` of all known transfers so a split
  is attributed proportionally. `_build_candidate` receives it.
- Value tracing takes `onward_pool` as an optional third argument. Without it
  the path edges are used, which overstates the traced amount.
- Two engine bugs were found and fixed by the tests: `get_edge_data` returns
  `{key: attrs}` (one level, not nested) and `out_edges(keys=True, data=True)`
  returns 4-tuples, not 3. Edge traversal is now centralised in
  `builder.iter_edge_transfers`.

## Constraints to keep respecting

- Every data point carries an `evidence_tag`: observed, derived, inferred.
- Never a single fraud score or risk percentage. Four separate confidence
  entries only.
- An exchange link is not complicity. Never call a service fraudulent,
  criminal, guilty or complicit.
- Shared infrastructure never implies common ownership.
- Abstention is a valid result and must be shown.
- No emojis, decorative Unicode, arrows, exclamation marks. Sentence case.
  ASCII hyphens only.
- Never invent exchange addresses, transaction hashes or citations. Synthetic
  fixtures must be clearly marked.
- No placeholders. Deferred work goes in `docs/limitations.md` and raises
  `NotImplementedError`.
- Log decisions in `docs/decisions.md`.
- Functions under about 50 lines, docstrings on public APIs, no debug prints.
