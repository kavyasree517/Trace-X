# Architecture and design decisions

## Record format
Each decision records context, alternatives considered, chosen approach, and rationale.

## DEC-001: Separation of chain facts from investigative interpretation
- Status: Accepted
- Context: Blockchain analytics tools often mix raw on-chain events with heuristic risk labels, producing unverifiable verdicts.
- Decision: Every claim-bearing data point is explicitly tagged with `evidence_tag`: `observed` (immutable ledger event), `derived` (deterministic calculation), or `inferred` (heuristic or statistical rule). No single composite fraud score or probability is calculated or displayed. <!-- copy-lint: allow -->
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

## DEC-004: Unverifiable label entries are deleted, not corrected
- Status: Accepted
- Context: The label registry carried a mixer entry whose address failed EIP-55 checksum validation and whose source reference had never been confirmed against a public page. Correcting the checksum would have produced a plausible looking address that no one had verified.
- Decision: Delete the entry. Registry validation rejects an entry whose address fails checksum validation, and no entry may be added without a citable source reference and a last verified date.
- Consequences: The registry loads with no errors. Re-adding any address requires a source that can be checked by a reviewer, and the mixer break path is covered by clearly marked synthetic labels and fixtures instead.
- Alternatives considered: Repairing the checksum from memory was rejected because it would present an unverified value as verified. Keeping the entry with a warning was rejected because it would surface a label whose provenance could not be shown.

## DEC-005: Copy lint uses a narrow inline allow marker
- Status: Accepted
- Context: The specification requires the README to carry a claims-to-avoid list, and the design log must state that no composite score is produced. Both therefore have to quote prohibited phrases in order to prohibit them. The linter flagged them, but excluding those whole files would have left the rest of the README and the design log unchecked.
- Decision: A line may opt out with an inline `copy-lint: allow` marker, written as an HTML comment in Markdown so it does not render. Whole-file exclusions remain limited to the specification, the copy deck, and tests that assert the phrases are absent.
- Consequences: Every other line of every other file stays linted, including the rest of the README. `backend/tests/unit/test_copy_lint.py` verifies that the marker exempts only the marked line.
- Alternatives considered: Excluding `README.md` and `docs/decisions.md` wholesale was rejected because it would silently disable the guard across most user-facing prose. Rewording the claims so they avoid the literal phrases was rejected because it would make the prohibited list harder to check against the linter configuration.
