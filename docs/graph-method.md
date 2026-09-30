# Graph expansion and path tracing methodology

## Graph construction
The graph is represented as a directed multigraph $G = (V, E)$ using NetworkX. Nodes $v \in V$ correspond to canonical blockchain addresses, and edges $e = (u, v, k) \in E$ represent individual asset transfers identified by transaction hash and event log index.

## Bounded expansion
Expansion begins at the seed address (or specific anchoring transaction) and proceeds breadth-first up to `GRAPH_MAX_HOPS_DEFAULT` (maximum 6 hops). Traversal enforces:
1. Node budget: Default 500 nodes, hard ceiling 2000 nodes.
2. Edge budget: Default 2000 edges, hard ceiling 8000 edges.
3. Execution deadline: 90 seconds wall-clock time limit.
4. Hub non-expansion: Nodes with degree exceeding `GRAPH_HIGH_DEGREE_THRESHOLD` (default 200) are not expanded further.
5. Terminal stops: Known exchange hot wallets, deposit hubs, and mixers terminate forward traversal.

## Time-respecting path extraction
A valid path $P = (e_1, e_2, \dots, e_m)$ requires non-decreasing timestamps:
$$t(e_i) \le t(e_{i+1}) \quad \forall i \in \{1, \dots, m-1\}$$
Paths are pruned if value continuity falls below 0.05, and output is capped at the top 25 ranked paths per case.

## Value tracing methods
- Proportional tracing: Value downstream is calculated based on the ratio of input funds to total address balance over the transfer window.
- FIFO tracing: Value is traced chronologically, assigning incoming lots directly to consecutive outgoing transactions.
Traced values are tagged as `derived`. Both methods estimate movement and do not constitute legal proof of fungible unit identity.
