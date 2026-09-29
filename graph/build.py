from __future__ import annotations
from typing import Dict, List, Optional, Any, Set, Tuple
import networkx as nx

from graph.schema import (
    InfrastructureGraph,
    AssetNode,
    DependencyEdge,
    NodeType,
    EdgeType,
)
from data.seed_data import get_puri_infrastructure_graph


class DependencyGraphManager:
    """
    Manages the multi-layered infrastructure dependency graph:
    - Layer 1: Power grid (Substations -> Feeders -> Assets)
    - Layer 2: Road network and resupply paths (Depots -> Road Segments -> Assets)
    - Layer 3: Telecommunications and service dependencies (Towers -> Assets)
    """

    def __init__(self, infra_graph: InfrastructureGraph | None = None):
        self.infra_graph = infra_graph or get_puri_infrastructure_graph()
        self.node_dict: Dict[str, AssetNode] = {n.id: n for n in self.infra_graph.nodes}
        self.power_graph = nx.DiGraph()
        self.road_graph = nx.Graph()
        self.service_graph = nx.DiGraph()
        self.resupply_routes: Dict[str, Dict[str, Any]] = {}
        self._build_subgraphs()

    def _build_subgraphs(self) -> None:
        """Construct layer-specific NetworkX graphs."""
        for n in self.infra_graph.nodes:
            if n.type in (NodeType.SUBSTATION, NodeType.FEEDER, NodeType.HOSPITAL, NodeType.TOWER, NodeType.WATER_PUMP):
                self.power_graph.add_node(n.id, data=n)
            if n.type in (NodeType.ROAD_SEGMENT, NodeType.DEPOT, NodeType.HOSPITAL, NodeType.WATER_PUMP, NodeType.TOWER):
                self.road_graph.add_node(n.id, data=n)

        for edge in self.infra_graph.edges:
            if edge.type == EdgeType.POWERS:
                self.power_graph.add_edge(edge.src, edge.dst, attrs=edge.attrs)
            elif edge.type == EdgeType.ACCESSED_VIA:
                self.road_graph.add_edge(edge.src, edge.dst, attrs=edge.attrs)
            elif edge.type == EdgeType.SERVES:
                self.service_graph.add_edge(edge.src, edge.dst, attrs=edge.attrs)
            elif edge.type == EdgeType.RESUPPLIED_FROM:
                # Store pre-defined resupply paths
                route_key = f"{edge.src}->{edge.dst}"
                self.resupply_routes[route_key] = {
                    "depot_id": edge.src,
                    "target_id": edge.dst,
                    "road_path": edge.attrs.get("path", []),
                    "distance_km": edge.attrs.get("distance_km", 5.0),
                }

    def get_upstream_power_sources(self, node_id: str) -> List[str]:
        """Find immediate upstream power suppliers (feeders/substations)."""
        if node_id in self.power_graph:
            return list(self.power_graph.predecessors(node_id))
        return []

    def get_resupply_routes_for_target(self, target_id: str) -> List[Dict[str, Any]]:
        """Return all potential resupply routes leading to target."""
        return [
            r for r in self.resupply_routes.values()
            if r["target_id"] == target_id
        ]

    def get_all_power_dependent_assets(self) -> List[str]:
        """Return asset IDs that depend on grid power."""
        return [
            n.id for n in self.infra_graph.nodes
            if len(self.get_upstream_power_sources(n.id)) > 0
        ]
