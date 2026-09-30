# Demonstration script

## Purpose and limitations
This walkthrough guides evaluators through an end-to-end investigation workflow using synthetic fixtures on the mock adapter in demonstration mode.

## Step 1: Initialize service
1. Start containers via `docker-compose up` or run locally via `make dev`.
2. Verify service availability at `http://localhost:8000/api/v1/health`.

## Step 2: Open web interface
Navigate to `http://localhost:5173`. Confirm presence of:
- Product title and institutional overview.
- Single Ethereum chain selector.
- Monospace address input field with format validation.
- Additional details disclosure panel.

## Step 3: Direct exchange deposit analysis (Fixture 1)
1. Enter suspect address: `0x71C84102F0B9C9B47B95C3C8F27B8A049B64B171`.
2. Click "Check Wallet".
3. Observe background progression stages: Retrieval -> Graph -> Attribution -> Behavior -> Corroboration -> Assembly.

## Step 4: Review confidence panel
Examine the four independent evaluation panels:
1. Path evidence: Confirmed chronological transfers.
2. Attribution confidence: Verified label match.
3. Behavioral signals: Pattern descriptions with standard disclaimer.
4. Corroboration strength: Cross-case overlap metrics.

## Step 5: Path graph and edge table
Inspect the React Flow visualization and tabular transfer view, verifying edge timestamps, assets, amounts, and transaction hashes.

## Step 6: Entity attribution provenance
Review the destination entity card, source verification level, and provenance metadata.

## Step 7: Export forensic dossier
Click "Export Report (PDF)". Verify the generated document adheres to ReportLab forensic formatting with an intact SHA-256 hash.

## Step 8: Mixer break abstention (Fixture 4)
Submit mixer interaction fixture. Verify the system abstains with `insufficient_data` and notes `mixer_interaction` rather than guessing destinations.
