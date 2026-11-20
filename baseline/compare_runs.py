"""Compare two local Retro* runs, ignoring elapsed time and object identities."""

import argparse
import json
import pickle
from pathlib import Path

from syntheseus.search.graph.and_or import AndNode


def tree_signature(graph, node, *, through_call=None):
    if isinstance(node, AndNode):
        label = ("reaction", node.reaction.reaction_smiles, node.reaction.metadata["probability"])
    else:
        label = ("molecule", node.mol.smiles, node.mol.metadata["is_purchasable"])
    children = sorted(
        tree_signature(graph, child, through_call=through_call)
        for child in graph.successors(node)
        if through_call is None or child.data["num_calls_rxn_model"] <= through_call
    )
    # Final expansion/solution flags may reflect a call after the common prefix.
    flags = (node.is_expanded, node.has_solution) if through_call is None else ()
    return (label, flags, node.data["num_calls_rxn_model"], children)


def compare(first, second):
    results = []
    for folder in (first, second):
        with (folder / "graph.pkl").open("rb") as stream:
            graph = pickle.load(stream)
        root = graph.root_node
        stats = json.loads((folder / "stats.json").read_bytes())
        ranked = [(n.reaction.reaction_smiles, n.reaction.metadata["probability"])
                  for n in graph.successors(root)]
        results.append((stats, ranked, graph))
    (a, roots_a, graph_a), (b, roots_b, graph_b) = results
    if a["smiles"] != b["smiles"]:
        raise ValueError("The two graphs have different input targets.")
    calls = [a["rxn_model_calls_used"], b["rxn_model_calls_used"]]
    cutoff = min(calls)
    return {
        "target": a["smiles"],
        "same_root_proposals_and_scores_in_order": roots_a == roots_b,
        "same_tree_labels_scores_expansions_and_creation_calls": (
            tree_signature(graph_a, graph_a.root_node) == tree_signature(graph_b, graph_b.root_node)
        ),
        "common_model_calls": cutoff,
        "same_generated_nodes_edges_scores_through_common_calls": (
            tree_signature(graph_a, graph_a.root_node, through_call=cutoff)
            == tree_signature(graph_b, graph_b.root_node, through_call=cutoff)
        ),
        "node_counts": [a["num_nodes_in_final_tree"], b["num_nodes_in_final_tree"]],
        "model_calls": calls,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path, help="first local target directory")
    parser.add_argument("second", type=Path, help="second local target directory")
    args = parser.parse_args()
    print(json.dumps(compare(args.first, args.second), indent=2))
