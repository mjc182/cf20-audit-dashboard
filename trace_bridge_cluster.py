import argparse
import csv
import json
from collections import defaultdict, deque
from pathlib import Path

EDGES_FILE = Path("cell_transfer_edges.csv")

MANUAL_LABEL_FILES = [
    Path("wallet_label_priority_review.csv"),
    Path("known_wallet_labels.csv"),
]

OUT_EDGES = Path("bridge_cluster_edges.csv")
OUT_PATHS = Path("bridge_cluster_paths.csv")
OUT_TERMINALS = Path("bridge_cluster_terminal_endpoints.csv")
OUT_UNCLASSIFIED = Path("bridge_cluster_unclassified_wallets.csv")
OUT_SUMMARY = Path("bridge_cluster_summary.json")

SEED_WALLETS = {
    "0x4a831a8ebb160ad025d34a788c99e9320b9ab531": "Bridge intake / Bridge Token target",
    "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60": "Bridge aggregator",
    "0x50ebb0827aa80ba1a2a30b38581629996262d481": "Major distributor",
    "0x65def3ea531fd80354ec11c611ae4faa06068f27": "Downstream distributor",
    "0xd3ec4a0113091ed2b0a3edbfdf1476efe07c8539": "Downstream distributor",
    "0x71f95edf9dd132970036fa3202d313ac2a4b9468": "Downstream distributor",
    "0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5": "Consolidation wallet",
    "0x52105eee8e836ff9e60cb02c0a665cbe2fc3a30d": "Secondary distributor",
    "0x9c4cc862f51b1ba90485de3502aa058ca4331f32": "Router / exchange-like hub",
}

KNOWN_CEX = {
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Gate.io 1",
    "0x75e89d5979e4f6fba9f97c104c2f0afb3f1dcb88": "MEXC 1",
    "0x3cc936b795a188f0e246cbb2d74c5bd190aecf18": "MEXC 3",
    "0x2e8f79ad740de90dc5f5a9f0d8d9661a60725e64": "MEXC 5",
    "0x4982085c9e2f89f2ecb8131eca71afad896e89cb": "MEXC 13",
    "0xeacb50a28630a4c44a884158ee85cbc10d2b3f10": "BitMart 7",
}

KNOWN_DEX_ROUTERS = {
    "0x74de5d4fcbf63e00296fd95d33236b9794016631": "MetaMask: Swaps Spender",
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap Universal Router",
    "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch Aggregation Router V5",
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router 2",
    "0x9008d19f58aabd9ed0d60971565aa8510560ab41": "CoW Protocol Settlement",
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b": "Uniswap / router contract",
    "0xdef171fe48cf0115b1d80b88dc8eab59176fee57": "ParaSwap / router contract",
    "0x000000000035b5e5ad9019092c665357240f594e": "Aggregator / settlement contract",
}

KNOWN_LP_OR_POOL = {
    "0xa2c1e0237bf4b58bc9808a579715df57522f41b2": "PancakeSwap v3 WBNB/CELL Pool",
}

KNOWN_MEV_OR_SEARCHERS = {
    "0x6b75d8af000000e20b7a7ddf000ba900b4009a80": "MEV Bot",
}

TERMINAL_CLASSES = {"CEX", "DEX_ROUTER", "LP_OR_POOL", "MEV_OR_SEARCHER"}


def norm(addr):
    return str(addr or "").strip().lower()


def amount_num(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def short(addr):
    addr = str(addr)
    if len(addr) <= 18:
        return addr
    return addr[:10] + "..." + addr[-8:]


def normalize_class(value):
    value = str(value or "").strip().upper()
    aliases = {
        "CEX": "CEX",
        "EXCHANGE": "CEX",
        "CENTRALIZED_EXCHANGE": "CEX",
        "DEX": "DEX_ROUTER",
        "DEX_ROUTER": "DEX_ROUTER",
        "ROUTER": "DEX_ROUTER",
        "SWAP_ROUTER": "DEX_ROUTER",
        "AGGREGATOR": "DEX_ROUTER",
        "DEX_AGGREGATOR": "DEX_ROUTER",
        "LP": "LP_OR_POOL",
        "POOL": "LP_OR_POOL",
        "LP_OR_POOL": "LP_OR_POOL",
        "MEV": "MEV_OR_SEARCHER",
        "MEV_OR_SEARCHER": "MEV_OR_SEARCHER",
        "SEARCHER": "MEV_OR_SEARCHER",
        "BOT": "MEV_OR_SEARCHER",
        "BRIDGE": "BRIDGE_CLUSTER",
        "BRIDGE_CLUSTER": "BRIDGE_CLUSTER",
        "BRIDGE_WALLET": "BRIDGE_CLUSTER",
        "DISTRIBUTOR": "DISTRIBUTOR",
        "CUSTODY": "CUSTODY",
        "USER": "USER_WALLET",
        "USER_WALLET": "USER_WALLET",
        "UNKNOWN": "UNCLASSIFIED",
        "UNCLASSIFIED": "UNCLASSIFIED",
    }
    return aliases.get(value, value if value else "")


def build_base_labels():
    labels = {}
    classes = {}

    for addr, label in SEED_WALLETS.items():
        labels[norm(addr)] = label
        classes[norm(addr)] = "BRIDGE_CLUSTER"

    for addr, label in KNOWN_CEX.items():
        labels[norm(addr)] = label
        classes[norm(addr)] = "CEX"

    for addr, label in KNOWN_DEX_ROUTERS.items():
        labels[norm(addr)] = label
        classes[norm(addr)] = "DEX_ROUTER"

    for addr, label in KNOWN_LP_OR_POOL.items():
        labels[norm(addr)] = label
        classes[norm(addr)] = "LP_OR_POOL"

    for addr, label in KNOWN_MEV_OR_SEARCHERS.items():
        labels[norm(addr)] = label
        classes[norm(addr)] = "MEV_OR_SEARCHER"

    return labels, classes


def load_manual_labels(labels, classes):
    loaded = 0

    for path in MANUAL_LABEL_FILES:
        if not path.exists():
            continue

        with path.open(newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                addr = norm(r.get("address"))
                if not addr:
                    continue

                manual_label = (r.get("manual_label") or r.get("label") or r.get("name") or "").strip()
                manual_class = normalize_class(r.get("manual_class") or r.get("class") or r.get("type") or "")

                if manual_label:
                    labels[addr] = manual_label

                if manual_class:
                    classes[addr] = manual_class

                if manual_label or manual_class:
                    loaded += 1

    return loaded


KNOWN_LABELS, KNOWN_CLASSES = build_base_labels()
MANUAL_LABEL_COUNT = load_manual_labels(KNOWN_LABELS, KNOWN_CLASSES)


def label_for(addr):
    return KNOWN_LABELS.get(norm(addr), "")


def classify(addr):
    addr = norm(addr)
    if addr in KNOWN_CLASSES:
        return KNOWN_CLASSES[addr]
    return "UNCLASSIFIED"


def is_terminal(addr):
    return classify(addr) in TERMINAL_CLASSES


def load_edges():
    if not EDGES_FILE.exists():
        raise FileNotFoundError("Missing cell_transfer_edges.csv. Run build_cell_wallet_universe.py first.")

    outgoing = defaultdict(list)
    incoming = defaultdict(list)

    with EDGES_FILE.open(newline="") as f:
        reader = csv.DictReader(f)

        for r in reader:
            src = norm(r.get("from"))
            dst = norm(r.get("to"))

            if not src or not dst:
                continue

            amt = amount_num(r.get("amount_cell", r.get("amount", 0)))

            row = {
                "chain": r.get("chain", ""),
                "from": src,
                "to": dst,
                "amount_cell": amt,
                "txs": int(amount_num(r.get("txs", 0))),
                "sample_tx_hash": r.get("sample_tx_hash", r.get("sample", "")),
            }

            outgoing[src].append(row)
            incoming[dst].append(row)

    for addr in outgoing:
        outgoing[addr].sort(key=lambda x: x["amount_cell"], reverse=True)

    for addr in incoming:
        incoming[addr].sort(key=lambda x: x["amount_cell"], reverse=True)

    return outgoing, incoming


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-hops", type=int, default=5)
    parser.add_argument("--min-amount", type=float, default=1000.0)
    parser.add_argument("--max-edges-per-node", type=int, default=75)
    parser.add_argument("--include-small", action="store_true")
    args = parser.parse_args()

    outgoing, incoming = load_edges()
    min_amount = 0.0 if args.include_small else args.min_amount

    discovered_edges = []
    discovered_paths = []
    terminal_hits = defaultdict(
        lambda: {
            "address": "",
            "label": "",
            "class": "",
            "terminal_inflow_possible_cell": 0.0,
            "direct_edge_count": 0,
            "paths": 0,
            "sample_paths": [],
            "sample_tx_hashes": set(),
        }
    )

    reachable = {}
    expanded = set()
    queue = deque()

    for seed, seed_label in SEED_WALLETS.items():
        seed = norm(seed)
        queue.append(
            {
                "node": seed,
                "hop": 0,
                "path": [seed],
                "path_amount": None,
                "path_text": f"{short(seed)}",
            }
        )
        reachable[seed] = {
            "address": seed,
            "label": seed_label,
            "class": classify(seed),
            "first_seen_hop": 0,
            "in_cluster_seed": True,
        }

    while queue:
        state = queue.popleft()
        node = state["node"]
        hop = state["hop"]
        path = state["path"]
        path_amount = state["path_amount"]
        path_text = state["path_text"]

        if hop >= args.max_hops:
            continue

        if is_terminal(node):
            continue

        expand_key = (node, hop)
        if expand_key in expanded:
            continue
        expanded.add(expand_key)

        edges = outgoing.get(node, [])
        edges = [e for e in edges if e["amount_cell"] >= min_amount]
        edges = edges[: args.max_edges_per_node]

        for e in edges:
            src = e["from"]
            dst = e["to"]
            amt = e["amount_cell"]

            loop_detected = dst in path
            dst_class = classify(dst)
            dst_label = label_for(dst)
            next_path_amount = amt if path_amount is None else min(path_amount, amt)
            next_path = path + [dst]
            next_path_text = path_text + f" → {short(dst)}"

            edge_row = {
                "hop": hop + 1,
                "chain": e["chain"],
                "from": src,
                "from_label": label_for(src),
                "from_class": classify(src),
                "to": dst,
                "to_label": dst_label,
                "to_class": dst_class,
                "amount_cell": round(amt, 8),
                "path_amount_possible_cell": round(next_path_amount, 8),
                "txs": e["txs"],
                "sample_tx_hash": e["sample_tx_hash"],
                "path": next_path_text,
                "loop_detected": loop_detected,
                "terminal": is_terminal(dst),
            }

            discovered_edges.append(edge_row)
            discovered_paths.append(edge_row)

            if dst not in reachable:
                reachable[dst] = {
                    "address": dst,
                    "label": dst_label,
                    "class": dst_class,
                    "first_seen_hop": hop + 1,
                    "in_cluster_seed": False,
                }

            if is_terminal(dst):
                t = terminal_hits[dst]
                t["address"] = dst
                t["label"] = dst_label
                t["class"] = dst_class
                t["terminal_inflow_possible_cell"] += next_path_amount
                t["direct_edge_count"] += 1
                t["paths"] += 1

                if e["sample_tx_hash"]:
                    t["sample_tx_hashes"].add(e["sample_tx_hash"])

                if len(t["sample_paths"]) < 8:
                    t["sample_paths"].append(next_path_text)

                continue

            if not loop_detected:
                queue.append(
                    {
                        "node": dst,
                        "hop": hop + 1,
                        "path": next_path,
                        "path_amount": next_path_amount,
                        "path_text": next_path_text,
                    }
                )

    terminal_rows = []
    for addr, item in terminal_hits.items():
        terminal_rows.append(
            {
                "address": addr,
                "address_short": short(addr),
                "label": item["label"],
                "class": item["class"],
                "terminal_inflow_possible_cell": round(item["terminal_inflow_possible_cell"], 8),
                "direct_edge_count": item["direct_edge_count"],
                "paths": item["paths"],
                "sample_tx_hashes": " | ".join(sorted([x for x in item["sample_tx_hashes"] if x])[:10]),
                "sample_paths": " || ".join(item["sample_paths"]),
            }
        )

    terminal_rows.sort(key=lambda r: r["terminal_inflow_possible_cell"], reverse=True)

    unclassified_rows = []
    for addr, item in reachable.items():
        if item["class"] != "UNCLASSIFIED":
            continue

        out_amt = sum(e["amount_cell"] for e in outgoing.get(addr, []))
        in_amt = sum(e["amount_cell"] for e in incoming.get(addr, []))

        suggested_review = "normal review"
        if max(in_amt, out_amt) >= 100000:
            suggested_review = "large unclassified downstream wallet"
        if abs(in_amt - out_amt) <= max(in_amt, out_amt, 1) * 0.02 and max(in_amt, out_amt) >= 100000:
            suggested_review = "large balanced pass-through wallet"
        if len(outgoing.get(addr, [])) >= 100 and out_amt >= 100000:
            suggested_review = "high-activity unclassified routing wallet"

        unclassified_rows.append(
            {
                "address": addr,
                "address_short": short(addr),
                "first_seen_hop": item["first_seen_hop"],
                "incoming_cell_all_dataset": round(in_amt, 8),
                "outgoing_cell_all_dataset": round(out_amt, 8),
                "net_cell_all_dataset": round(in_amt - out_amt, 8),
                "incoming_edges": len(incoming.get(addr, [])),
                "outgoing_edges": len(outgoing.get(addr, [])),
                "suggested_review": suggested_review,
            }
        )

    unclassified_rows.sort(
        key=lambda r: (
            r["suggested_review"] != "normal review",
            r["outgoing_cell_all_dataset"],
            r["incoming_cell_all_dataset"],
        ),
        reverse=True,
    )

    edge_fields = [
        "hop",
        "chain",
        "from",
        "from_label",
        "from_class",
        "to",
        "to_label",
        "to_class",
        "amount_cell",
        "path_amount_possible_cell",
        "txs",
        "sample_tx_hash",
        "path",
        "loop_detected",
        "terminal",
    ]

    write_csv(OUT_EDGES, discovered_edges, edge_fields)
    write_csv(OUT_PATHS, discovered_paths, edge_fields)

    write_csv(
        OUT_TERMINALS,
        terminal_rows,
        [
            "address",
            "address_short",
            "label",
            "class",
            "terminal_inflow_possible_cell",
            "direct_edge_count",
            "paths",
            "sample_tx_hashes",
            "sample_paths",
        ],
    )

    write_csv(
        OUT_UNCLASSIFIED,
        unclassified_rows,
        [
            "address",
            "address_short",
            "first_seen_hop",
            "incoming_cell_all_dataset",
            "outgoing_cell_all_dataset",
            "net_cell_all_dataset",
            "incoming_edges",
            "outgoing_edges",
            "suggested_review",
        ],
    )

    summary = {
        "max_hops": args.max_hops,
        "min_amount": min_amount,
        "max_edges_per_node": args.max_edges_per_node,
        "manual_labels_loaded": MANUAL_LABEL_COUNT,
        "seed_wallet_count": len(SEED_WALLETS),
        "reachable_wallets": len(reachable),
        "discovered_edges": len(discovered_edges),
        "terminal_endpoint_count": len(terminal_rows),
        "unclassified_wallet_count": len(unclassified_rows),
        "terminal_classes": sorted(list(TERMINAL_CLASSES)),
        "known_cex_routes_cell_possible": sum(
            r["terminal_inflow_possible_cell"] for r in terminal_rows if r["class"] == "CEX"
        ),
        "known_dex_router_routes_cell_possible": sum(
            r["terminal_inflow_possible_cell"] for r in terminal_rows if r["class"] == "DEX_ROUTER"
        ),
        "known_mev_routes_cell_possible": sum(
            r["terminal_inflow_possible_cell"] for r in terminal_rows if r["class"] == "MEV_OR_SEARCHER"
        ),
        "important_note": (
            "Amounts are route-exposure evidence from an aggregated transfer graph. "
            "They are not exact final sale amounts because paths can overlap, loop, "
            "or terminate inside CEX custody where internal trades are off-chain."
        ),
        "outputs": {
            "edges": str(OUT_EDGES),
            "paths": str(OUT_PATHS),
            "terminal_endpoints": str(OUT_TERMINALS),
            "unclassified": str(OUT_UNCLASSIFIED),
            "summary": str(OUT_SUMMARY),
        },
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2))

    print("\n==============================")
    print("BRIDGE CLUSTER TRAVERSAL RESULT")
    print("==============================\n")

    print(f"Max hops:                  {args.max_hops}")
    print(f"Minimum edge amount:       {min_amount:,.2f} CELL")
    print(f"Max edges per node:        {args.max_edges_per_node}")
    print(f"Manual labels loaded:      {MANUAL_LABEL_COUNT:,}")
    print(f"Reachable wallets:         {len(reachable):,}")
    print(f"Discovered edges:          {len(discovered_edges):,}")
    print(f"Terminal endpoints:        {len(terminal_rows):,}")
    print(f"Unclassified wallets:      {len(unclassified_rows):,}")

    print("\nTop terminal endpoints:")
    for r in terminal_rows[:25]:
        print(
            f"{r['terminal_inflow_possible_cell']:,.2f} CELL | "
            f"{r['class']} | {r['label']} | {r['address']}"
        )

    print("\nTop unclassified wallets to review:")
    for r in unclassified_rows[:25]:
        print(
            f"out={r['outgoing_cell_all_dataset']:,.2f} | "
            f"in={r['incoming_cell_all_dataset']:,.2f} | "
            f"hop={r['first_seen_hop']} | "
            f"{r['address']} | {r['suggested_review']}"
        )

    print("\nSaved:")
    print(f"- {OUT_EDGES}")
    print(f"- {OUT_PATHS}")
    print(f"- {OUT_TERMINALS}")
    print(f"- {OUT_UNCLASSIFIED}")
    print(f"- {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
