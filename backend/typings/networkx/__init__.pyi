"""Minimal local type declarations for the NetworkX surface TRACE-X uses.

NetworkX ships no type information. These declarations cover only the calls
made by the graph engine, so that mypy strict can verify our own code. Nodes
are always canonical address strings in TRACE-X.
"""

from collections.abc import Hashable, Iterable, Iterator
from typing import Any

NodeKey = str

NodeData = dict[str, Any]
GraphData = dict[str, Any]


class MultiDiGraph:
    """Directed graph permitting several edges between the same node pair."""

    def __init__(self, incoming_graph_data: Any = None, **attr: Any) -> None: ...

    def __contains__(self, n: object) -> bool: ...

    def __len__(self) -> int: ...

    def __iter__(self) -> Iterator[NodeKey]: ...

    def __getitem__(self, n: NodeKey) -> NodeData: ...

    def add_node(self, node_for_adding: NodeKey, **attr: Any) -> None: ...

    def add_nodes_from(self, nodes: Iterable[tuple[NodeKey, Any]], **attr: Any) -> None: ...

    def add_edge(
        self,
        u_of_edge: NodeKey,
        v_of_edge: NodeKey,
        key: Hashable | None = None,
        **attr: Any,
    ) -> Hashable: ...

    def get_edge_data(self, u: NodeKey, v: NodeKey, key: Hashable | None = None) -> Any: ...

    def successors(self, node: NodeKey) -> Iterable[NodeKey]: ...

    def predecessors(self, node: NodeKey) -> Iterable[NodeKey]: ...

    def out_edges(
        self, nbunch: Any = None, data: bool = False, keys: bool = False
    ) -> Iterable[tuple[Any, ...]]: ...

    def in_edges(
        self, nbunch: Any = None, data: bool = False, keys: bool = False
    ) -> Iterable[tuple[Any, ...]]: ...

    def edges(
        self, nbunch: Any = None, data: bool = False, keys: bool = False
    ) -> Iterable[tuple[Any, ...]]: ...

    @property
    def nodes(self) -> Any: ...

    @property
    def graph(self) -> GraphData: ...

    def number_of_nodes(self) -> int: ...

    def number_of_edges(self, u: Any = None, v: Any = None) -> int: ...

    def in_degree(self, nbunch: Any = None) -> Any: ...

    def out_degree(self, nbunch: Any = None) -> Any: ...

    def degree(self, nbunch: Any = None) -> Any: ...

    def subgraph(self, nodes: Iterable[NodeKey]) -> MultiDiGraph: ...

    def is_directed(self) -> bool: ...

    def is_multigraph(self) -> bool: ...

    def copy(self) -> MultiDiGraph: ...

    def to_undirected(self, reciprocal: bool = False, as_view: bool = False) -> Any: ...


class DiGraph(MultiDiGraph):
    """Directed graph permitting at most one edge per node pair."""


def relabel_nodes(graph: MultiDiGraph, mapping: dict[Any, Any], copy: bool = True) -> Any: ...
