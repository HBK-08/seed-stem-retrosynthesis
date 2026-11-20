"""Print root proposals and complete routes from a local Retro* search graph."""

import argparse
import json
import pickle
from pathlib import Path

from syntheseus.search.analysis.route_extraction import iter_routes_time_order
from syntheseus.search.graph.and_or import AndNode


def summarize(graph):
    root = graph.root_node
    proposals = []
    for node in graph.successors(root):
        proposals.append({
            "reaction": node.reaction.reaction_smiles,
            "model_probability": node.reaction.metadata.get("probability"),
            "precursors": [
                {"smiles": child.mol.smiles, "in_stock": child.mol.metadata["is_purchasable"],
                 "expanded": child.is_expanded, "solved": child.has_solution}
                for child in graph.successors(node)
            ],
        })
    routes = []
    if root.has_solution:
        for nodes in iter_routes_time_order(graph, max_routes=5):
            steps = sorted((n for n in nodes if isinstance(n, AndNode)),
                           key=lambda n: (-n.depth, n.reaction.reaction_smiles))
            routes.append([n.reaction.reaction_smiles for n in steps])
    return {"target": root.mol.smiles, "stock_closed": root.has_solution,
            "root_proposals_in_search_graph": proposals, "routes_in_discovery_order": routes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path, help="graph.pkl from your own Syntheseus run")
    args = parser.parse_args()
    with args.graph.open("rb") as stream:
        print(json.dumps(summarize(pickle.load(stream)), indent=2, allow_nan=False))
