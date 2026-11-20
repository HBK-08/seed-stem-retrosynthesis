"""Check a saved local search against the stock and reconstruct the five cutoffs."""

import argparse
import hashlib
import json
import pickle
import sqlite3
from functools import lru_cache
from pathlib import Path

import networkx as nx

from prepare_stock import STOCK_SHA256


def audit(run, db):
    inputs = json.loads((run / "input.json").read_text(encoding="utf-8"))
    result = json.loads((run / "result.json").read_text(encoding="utf-8"))
    with (run / "graph.pkl").open("rb") as stream:
        graph = pickle.load(stream)
    graph.assert_validity()
    assert graph.root_mol.smiles == inputs["canonical_smiles"]
    assert len(graph) == result["graph_nodes"]
    assert db.execute("SELECT sha256 FROM source").fetchone()[0] == inputs["stock"]["sha256"] == STOCK_SHA256
    target_file = Path(__file__).with_name("targets.smi").read_bytes()
    assert hashlib.sha256(target_file).hexdigest() == inputs["target_list_sha256"]
    assert target_file.decode("ascii").splitlines()[inputs["index"]] == inputs["upstream_smiles"]

    @lru_cache(maxsize=None)
    def in_stock(smiles):
        return db.execute("SELECT 1 FROM stock WHERE smiles=?", (smiles,)).fetchone() is not None

    born = {}
    closed = []
    for node in graph.nodes():
        born[node] = (node.creation_time - graph.root_node.creation_time).total_seconds()
        for mol in node.mols:
            assert in_stock(mol.smiles) == mol.metadata["is_purchasable"]
        if all(in_stock(mol.smiles) for mol in node.mols):
            closed.append(node)

    assert in_stock(graph.root_mol.smiles) == inputs["target_in_stock"]
    assert len(closed) == result["terminal_states_all_in_stock"]
    first = min((born[node] for node in closed), default=None)
    assert first == result["first_solution_s"]
    assert graph.root_node.has_solution == bool(closed)
    if first is not None:
        # Replay the recorded route forward from stock, independent of graph traversal.
        available = set(result["first_route_stock_leaves"])
        assert all(in_stock(smiles) for smiles in available)
        for reaction in result["first_route_reactions_in_forward_order"]:
            reactants, _, product = reaction.split(">")
            assert set(reactants.split(".")) <= available
            available.add(product)
        assert graph.root_mol.smiles in available
    else:
        assert not result["first_route_reactions_in_forward_order"] and not result["first_route_stock_leaves"]

    children = list(graph.successors(graph.root_node))
    cutoffs = []
    for minute in (1, 2, 5, 10, 30):
        cutoff = minute * 60
        seen = [node for node, t in born.items() if t <= cutoff]
        solved = first is not None and first <= cutoff
        assert solved == result["solved_by_minute"][str(minute)]
        cutoffs.append({
            "minute": minute, "solved": solved, "nodes": len(seen),
            "max_depth": max(node.depth for node in seen),
            "root_children_with_descendants": sum(
                any(born[grandchild] <= cutoff for grandchild in graph.successors(child))
                for child in children
            ),
        })
    return {
        "distinct_molecules_checked_against_stock": in_stock.cache_info().currsize,
        "distinct_molecule_sets": len({node.mols for node in born}),
        "root_children_in_final_graph": len(children), "cutoffs": cutoffs,
        "expanded_root_children": [
            {
                "position_in_graph": i,
                "reaction": graph._graph.edges[graph.root_node, child]["reaction"].reaction_smiles,
                "policy_score": child.data.get("policy_score"),
                "descendants": len(nx.descendants(graph._graph, child)),
            }
            for i, child in enumerate(children, start=1) if child.is_expanded
        ],
        "all_nodes_including_overrun": len(graph),
        "max_depth_including_overrun": max(node.depth for node in born),
        "expanded_nodes_including_overrun": sum(node.is_expanded for node in born),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--stock", type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(args.stock.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        print(json.dumps(audit(args.run, db), indent=2))
    finally:
        db.close()
