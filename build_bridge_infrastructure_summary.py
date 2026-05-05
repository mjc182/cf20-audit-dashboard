import csv
import json
from pathlib import Path

OUT = Path("bridge_infrastructure_summary.json")
TERMINALS = Path("bridge_cluster_terminal_endpoints.csv")
UNCLASSIFIED = Path("bridge_cluster_unclassified_wallets.csv")
CLUSTER_SUMMARY = Path("bridge_cluster_summary.json")
KNOWN_LABELS = Path("known_wallet_labels.csv")
MARKET_SUMMARY = Path("bridge_market_route_summary.json")


def fnum(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except Exception:
        return default


def load_csv(path):
    if not path.exists():
        return []
    try:
        with path.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def sum_terminal_class(class_name):
    total = 0.0
    for r in load_csv(TERMINALS):
        if r.get("class") == class_name:
            total += fnum(r.get("terminal_inflow_possible_cell"))
    return total


def main():
    cluster = load_json(CLUSTER_SUMMARY)
    labels = load_csv(KNOWN_LABELS)
    labels_by_addr = {r.get("address", "").lower(): r for r in labels if r.get("address")}

    bridge_lock = labels_by_addr.get("0xfd64fa5976687c2048f08f5df89c9a78e31df680", {
        "address": "0xfd64fa5976687c2048f08f5df89c9a78e31df680",
        "manual_label": "Bridge Lock/Unlock Contract",
        "manual_class": "BRIDGE_CLUSTER",
        "notes": "Etherscan method history shows Lock Token and Unlock Token; routes to 0x4A831 bridge intake and 0x35ce bridge aggregator",
    })

    terminals = load_csv(TERMINALS)
    terminal_summary = []
    for r in terminals:
        terminal_summary.append({
            "address": r.get("address", ""),
            "label": r.get("label", ""),
            "class": r.get("class", ""),
            "route_exposure_possible_cell": fnum(r.get("terminal_inflow_possible_cell")),
            "paths": int(fnum(r.get("paths"))),
            "direct_edge_count": int(fnum(r.get("direct_edge_count"))),
        })
    terminal_summary.sort(key=lambda r: r["route_exposure_possible_cell"], reverse=True)

    top_unclassified = []
    for r in load_csv(UNCLASSIFIED)[:25]:
        top_unclassified.append({
            "address": r.get("address", ""),
            "first_seen_hop": int(fnum(r.get("first_seen_hop"))),
            "incoming_cell_all_dataset": fnum(r.get("incoming_cell_all_dataset")),
            "outgoing_cell_all_dataset": fnum(r.get("outgoing_cell_all_dataset")),
            "net_cell_all_dataset": fnum(r.get("net_cell_all_dataset")),
            "suggested_review": r.get("suggested_review", ""),
        })

    summary = {
        "bridge_contracts": [
            {
                "address": "0xfd64fa5976687c2048f08f5df89c9a78e31df680",
                "label": bridge_lock.get("manual_label", "Bridge Lock/Unlock Contract"),
                "class": bridge_lock.get("manual_class", "BRIDGE_CLUSTER"),
                "evidence": "Etherscan transaction methods show Lock Token and Unlock Token. Observed unlock routes include 0x4A831... and 0x35ce....",
                "audit_status": "Bridge lock/unlock infrastructure identified; not full reserve reconciliation by itself.",
            },
            {
                "address": "0x4a831a8ebb160ad025d34a788c99e9320b9ab531",
                "label": "Bridge intake / Bridge Token target",
                "class": "BRIDGE_CLUSTER",
                "evidence": "Etherscan shows repeated Bridge Token calls; address held a large CELL balance during manual inspection.",
                "audit_status": "Bridge-facing intake/router identified.",
            },
            {
                "address": "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60",
                "label": "Bridge aggregator",
                "class": "BRIDGE_CLUSTER",
                "evidence": "Receives from bridge intake and routes to 0x50ebb..., 0x52105..., and 0xda8a....",
                "audit_status": "Aggregator/distributor bridge route identified.",
            },
        ],
        "bridge_cluster": [
            {"address": "0x50ebb0827aa80ba1a2a30b38581629996262d481", "label": "Major distributor"},
            {"address": "0x65def3ea531fd80354ec11c611ae4faa06068f27", "label": "Downstream distributor"},
            {"address": "0xd3ec4a0113091ed2b0a3edbfdf1476efe07c8539", "label": "Downstream distributor"},
            {"address": "0x71f95edf9dd132970036fa3202d313ac2a4b9468", "label": "Downstream distributor"},
            {"address": "0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5", "label": "Consolidation wallet"},
            {"address": "0x52105eee8e836ff9e60cb02c0a665cbe2fc3a30d", "label": "Secondary distributor"},
            {"address": "0x9c4cc862f51b1ba90485de3502aa058ca4331f32", "label": "Router / exchange-like hub"},
        ],
        "manual_findings": [
            {"finding": "Bridge lock/unlock endpoint identified", "status": "New evidence", "details": "0xfd64... shows Lock Token and Unlock Token methods and routes to known bridge infrastructure."},
            {"finding": "CEX routes identified", "status": "Strongly supported", "details": "Traversal reaches Gate.io and MEXC-labelled wallets."},
            {"finding": "DEX / swap routes identified", "status": "Strongly supported", "details": "Traversal reaches Uniswap, MetaMask Swaps, 1inch, ParaSwap, CoW, and other router/settlement endpoints."},
            {"finding": "Exact sale amount", "status": "Not directly visible", "details": "Route exposure does not equal exact sale volume because paths can overlap/loop and CEX internal trades are off-chain."},
        ],
        "cluster_metrics": {
            "reachable_wallets": cluster.get("reachable_wallets"),
            "discovered_edges": cluster.get("discovered_edges"),
            "terminal_endpoint_count": cluster.get("terminal_endpoint_count"),
            "unclassified_wallet_count": cluster.get("unclassified_wallet_count"),
            "manual_labels_loaded": cluster.get("manual_labels_loaded"),
            "known_cex_routes_cell_possible": cluster.get("known_cex_routes_cell_possible", sum_terminal_class("CEX")),
            "known_dex_router_routes_cell_possible": cluster.get("known_dex_router_routes_cell_possible", sum_terminal_class("DEX_ROUTER")),
            "known_mev_routes_cell_possible": cluster.get("known_mev_routes_cell_possible", sum_terminal_class("MEV_OR_SEARCHER")),
        },
        "terminal_summary": terminal_summary,
        "top_unclassified": top_unclassified,
        "important_note": (
            "All route amounts are route-exposure evidence from an aggregated graph. "
            "They are not exact final sale amounts. CEX deposits prove custody routing, "
            "but exchange-internal trades are off-chain. DEX/router paths require transaction-level "
            "log verification to quantify executed swaps."
        ),
    }

    OUT.write_text(json.dumps(summary, indent=2))
    print(f"Saved {OUT}")
    print("Bridge lock/unlock infrastructure identified: 0xfd64...")
    print("Bridge intake/router identified: 0x4A831...")
    print("Market routes identified: CEX + DEX + MEV endpoints")


if __name__ == "__main__":
    main()
