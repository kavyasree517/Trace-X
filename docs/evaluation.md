# Evaluation framework

## Evaluation objectives
The benchmark suite evaluates:
1. Behavioral pattern detection accuracy against published research benchmarks.
2. Path relevance and pruning efficiency (unfiltered traversal vs report-conditioned expansion).
3. Attribution precision and correct abstention rates.
4. Corroboration accuracy against known multi-report syndicates.
5. Algorithmic reproducibility across independent runs.

## Benchmark datasets
Evaluation uses public peer-reviewed datasets with documented licenses, supplemented with synthetic graph generators with known ground truth. Research dataset results are never conflated with live victim report performance.

## Metrics
- Behavioral models: Precision, Recall, F1-score, Precision-Recall AUC, False Positive Rate.
- Graph relevance: Relevant transfers at rank $k$, expansion runtime, edge pruning percentage.
- Attribution: Accuracy on verified labels, Brier calibration error, abstention rate on unlabelled nodes.
- Corroboration: Pairwise link precision and recall, false association rate on shared infrastructure.

## Ablation studies
- Ablation 1: Removal of incident-report time conditioning.
- Ablation 2: Removal of multi-factor provenance scoring (flat label matching).
- Ablation 3: Disabling cross-case corroboration.
- Ablation 4: Removal of temporal ordering constraints.
