"""Run one original SimpRetro target for the full Fig. 4a time budget."""

import argparse
import hashlib
import json
import math
import os
import pickle
import random
import sqlite3
import threading
import time
from importlib.metadata import version
from pathlib import Path

from omegaconf import OmegaConf
from syntheseus import Molecule
from syntheseus.cli.search import SearchConfig, search_algorithm_config_to_kwargs
from syntheseus.reaction_prediction.utils.config import get_config
from syntheseus.reaction_prediction.utils.misc import set_random_seed
from syntheseus.reaction_prediction.utils.model_loading import get_model
from syntheseus.search.analysis.solution_time import get_first_solution_time
from syntheseus.search.mol_inventory import BaseMolInventory
from prepare_stock import STOCK_SHA256

HERE = Path(__file__).resolve().parent
MINUTES = (1, 2, 5, 10, 30)
TARGETS_SHA256 = "2803ed381b5908d785333231263f78dd4ef673ed00c13dd675f01d1f07f34683"


class Stock(BaseMolInventory):
    def __init__(self, path):
        self.db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        self.db.row_factory = sqlite3.Row

    def is_purchasable(self, mol):
        return self.db.execute("SELECT 1 FROM stock WHERE smiles=?", (mol.smiles,)).fetchone() is not None


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def analyze(graph):
    start = graph.root_node.creation_time
    closed = []
    for node in graph.nodes():
        node.data["analysis_time"] = (node.creation_time - start).total_seconds()
        if all(mol.metadata["is_purchasable"] for mol in node.mols):
            closed.append(node)
    first = get_first_solution_time(graph)
    route, leaves = [], []
    if closed:
        node = min(closed, key=lambda n: n.creation_time)
        assert math.isclose(first, node.data["analysis_time"])
        leaves = sorted(mol.smiles for mol in node.mols)
        while node is not graph.root_node:
            parent, = graph.predecessors(node)
            route.append(graph._graph.edges[parent, node]["reaction"].reaction_smiles)
            node = parent
    else:
        assert not math.isfinite(first)
    return {
        "first_solution_s": first if math.isfinite(first) else None,
        "solved_by_minute": {str(m): first <= 60*m for m in MINUTES},
        "terminal_states_all_in_stock": len(closed),
        "first_route_reactions_in_forward_order": route,
        "first_route_stock_leaves": leaves,
        "root_reactions_in_graph": [
            graph._graph.edges[graph.root_node, child]["reaction"].reaction_smiles
            for child in graph.successors(graph.root_node)
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--index", type=int, default=0, help="zero-based index in original target file")
    args = parser.parse_args()
    raw = (HERE / "targets.smi").read_bytes()
    if hashlib.sha256(raw).hexdigest() != TARGETS_SHA256:
        raise ValueError("Target file differs from the pinned author release.")
    targets = raw.decode("ascii").splitlines()
    if not 0 <= args.index < len(targets):
        parser.error("Target index out of range")
    target = Molecule(targets[args.index])
    cfg = get_config(["--config", str(HERE / "search.yml")], SearchConfig)
    stock = Stock(args.stock)
    source = dict(stock.db.execute("SELECT * FROM source").fetchone())
    if source["sha256"] != STOCK_SHA256:
        raise ValueError("Inventory does not match the pinned author download.")
    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out / "input.json", {
        "index": args.index, "upstream_smiles": targets[args.index], "canonical_smiles": target.smiles,
        "target_in_stock": stock.is_purchasable(target), "target_list_sha256": TARGETS_SHA256,
        "stock": source, "versions": {p: version(p) for p in ("syntheseus", "retrochimera", "torch", "rdkit")},
        "threads_and_hash_seed": {k: os.getenv(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "PYTHONHASHSEED")},
        "random_seed": 0, "config": OmegaConf.to_container(cfg, enum_to_str=True),
    })
    set_random_seed(0)
    load = time.monotonic()
    model = get_model(cfg, num_gpus=int(cfg.use_gpu), use_cache=cfg.reaction_model_use_cache,
                      default_num_results=cfg.num_top_results)
    planner = cfg.search_algorithm.value(
        reaction_model=model, mol_inventory=stock, random_state=random.Random(0),
        **search_algorithm_config_to_kwargs(cfg),
    )
    planner.reset()
    start = time.monotonic()
    print(f"Model ready. Starting {cfg.time_limit_s:g}s search for target {args.index}.", flush=True)
    graph = planner.create_graph(target)
    done = threading.Event()

    def report_progress():
        while not done.wait(60):
            print(f"Search {time.monotonic()-start:.0f}s: {model.num_calls()} model calls, "
                  f"{len(graph)} nodes, root solved={graph.root_node.has_solution}", flush=True)

    progress = threading.Thread(target=report_progress, daemon=True)
    progress.start()
    try:
        planner.run_from_graph(graph)
    finally:
        done.set()
        progress.join()
    elapsed = time.monotonic() - start
    with (args.out / "graph.pkl").open("wb") as stream:
        pickle.dump(graph, stream)
    report = analyze(graph)
    report.update(index=args.index, model_and_planner_setup_s=start-load, search_wall_s=elapsed,
                  model_calls=model.num_calls(), graph_nodes=len(graph))
    write_json(args.out / "result.json", report)
    print("Completed:", {k: report[k] for k in ("first_solution_s", "model_calls", "graph_nodes", "search_wall_s")})
    stock.db.close()


if __name__ == "__main__":
    main()
