# Architecture and design decisions

## Record format
Each decision records context, alternatives considered, chosen approach, and rationale.

## DEC-001: Separation of chain facts from investigative interpretation
- Status: Accepted
- Context: Blockchain analytics tools often mix raw on-chain events with heuristic risk labels, producing unverifiable verdicts.
- Decision: Every claim-bearing data point is explicitly tagged with `evidence_tag`: `observed` (immutable ledger event), `derived` (deterministic calculation), or `inferred` (heuristic or statistical rule). No single composite fraud score or probability is calculated or displayed.
- Consequences: UI and API must expose separate panels for path evidence, attribution confidence, behavioral signals, and corroboration strength.

## DEC-002: Rejection of decorative styling and subjective language
- Status: Accepted
- Context: Forensic and public sector investigation tools require neutral presentation that resists confirmation bias.
- Decision: Pure sentence-case English, zero emojis or decorative glyphs, strict copy linter against accusatory phrases, and institutional color palettes meeting WCAG 2.1 AA contrast requirements.
- Consequences: All user interface strings originate from a single centralized copy dictionary checked by automated tests.

## DEC-003: Default execution in mock adapter and demonstration mode
- Status: Accepted
- Context: Local evaluation and demonstration must function deterministically without external network access or paid API keys.
- Decision: Default configuration uses `DATA_ADAPTER=mock` and `DEMO_MODE=true` with pre-computed synthetic fixtures. Production live analysis requires explicit environment configuration.
- Consequences: Synthetic labels and simulated paths are clearly marked with `level_0_synthetic` verification levels and demo notices.
