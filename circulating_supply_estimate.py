#!/usr/bin/env python3
import csv
import json
from decimal import Decimal
from pathlib import Path

def D(x, default="0"):
    try:
        if x is None or x == "":
            return Decimal(default)
        return Decimal(str(x))
    except Exception:
        return Decimal(default)

def load_json(path):
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())

def read_csv(path):
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="") as f:
        return list(csv.DictReader(f))

reserve = load_json("reserve_backing_reconciliation.json")

totals = reserve.get("totals", {}) if isinstance(reserve, dict) else {}

eth_total = D(
    totals.get("eth_total_supply_cell")
    or reserve.get("eth_total_supply_cell")
    or "30300000"
)

bsc_total = D(
    totals.get("bsc_total_supply_cell")
    or reserve.get("bsc_total_supply_cell")
    or "33300000"
)

raw_total = eth_total + bsc_total

eth_backing_candidates = D(
    totals.get("eth_backing_candidate_included_cell")
    or reserve.get("eth_backing_candidate_included_cell")
    or "0"
)

bsc_backing_candidates = D(
    totals.get("bsc_backing_candidate_included_cell")
    or reserve.get("bsc_backing_candidate_included_cell")
    or "0"
)

# Known verified route exposure. This is NOT excluded from circulating supply.
gateio_route_exposure = D("2596567.55466338")

# Known current observed unresolved/held old-CELL is separate old token, not current CELL circulating supply.
old_cell_a9ad_held = D("2625551.2")

# Conservative method:
# Exclude only verified backing/reserve candidates.
# Do NOT exclude exchange-routed, distributor, high-activity, or unresolved wallets.
conservative_non_circulating = eth_backing_candidates + bsc_backing_candidates
conservative_circulating_estimate = raw_total - conservative_non_circulating

# BSC-focused view:
bsc_conservative_non_circulating = bsc_backing_candidates
bsc_conservative_circulating_estimate = bsc_total - bsc_conservative_non_circulating

# Backing-adjusted exposure view:
# How much BSC supply is not currently reconciled by verified ETH backing candidates.
bsc_unbacked_or_unreconciled = bsc_total - eth_backing_candidates

summary = {
    "methodology": {
        "conservative_circulating_definition": (
            "Raw contract supply minus only verified reserve/backing/locked candidates. "
            "Exchange-routed, distributor, high-activity, unresolved, or unlabelled wallets are not excluded."
        ),
        "important_caveat": (
            "This is an on-chain estimate, not an official circulating supply. "
            "A definitive circulating supply requires verified lockups, reserve wallets, treasury wallets, "
            "market-maker wallets, exchange balances, and vesting schedules."
        ),
    },
    "inputs": {
        "eth_total_supply_cell": str(eth_total),
        "bsc_total_supply_cell": str(bsc_total),
        "raw_eth_plus_bsc_contract_supply_cell": str(raw_total),
        "eth_verified_backing_candidate_balances_cell": str(eth_backing_candidates),
        "bsc_verified_backing_candidate_balances_cell": str(bsc_backing_candidates),
        "verified_gateio_route_exposure_cell": str(gateio_route_exposure),
    },
    "estimates": {
        "conservative_non_circulating_cell": str(conservative_non_circulating),
        "conservative_circulating_supply_estimate_cell": str(conservative_circulating_estimate),
        "bsc_conservative_circulating_supply_estimate_cell": str(bsc_conservative_circulating_estimate),
        "bsc_supply_minus_verified_eth_backing_candidates_cell": str(bsc_unbacked_or_unreconciled),
    },
    "audit_interpretation": (
        "Under the current verified evidence set, only a small amount of ETH-side candidate backing is verified. "
        "The BSC supply remains largely unreconciled by verified backing candidates, so most BSC supply should be "
        "treated as potentially circulating or distribution-exposed unless additional locked/reserve wallets are verified."
    ),
}

Path("circulating_supply_estimate.json").write_text(json.dumps(summary, indent=2))

rows = [
    {
        "metric": "ETH totalSupply",
        "amount_cell": str(eth_total),
        "classification": "contract_supply",
        "notes": "Ethereum CELL contract supply.",
    },
    {
        "metric": "BSC totalSupply",
        "amount_cell": str(bsc_total),
        "classification": "contract_supply",
        "notes": "BSC CELL v2 contract supply.",
    },
    {
        "metric": "Raw ETH+BSC contract supply",
        "amount_cell": str(raw_total),
        "classification": "raw_supply",
        "notes": "Simple sum of contract-level supplies across ETH and BSC.",
    },
    {
        "metric": "Verified backing/reserve candidates",
        "amount_cell": str(conservative_non_circulating),
        "classification": "excluded_non_circulating_conservative",
        "notes": "Only verified reserve/backing candidates are excluded.",
    },
    {
        "metric": "Conservative circulating supply estimate",
        "amount_cell": str(conservative_circulating_estimate),
        "classification": "circulating_estimate",
        "notes": "Raw supply minus verified backing/reserve candidates.",
    },
    {
        "metric": "BSC conservative circulating estimate",
        "amount_cell": str(bsc_conservative_circulating_estimate),
        "classification": "bsc_circulating_estimate",
        "notes": "BSC supply minus verified BSC backing candidates.",
    },
    {
        "metric": "BSC supply minus verified ETH backing candidates",
        "amount_cell": str(bsc_unbacked_or_unreconciled),
        "classification": "unreconciled_bsc_supply",
        "notes": "BSC supply not reconciled by currently verified ETH backing candidates.",
    },
    {
        "metric": "Verified Gate.io route exposure",
        "amount_cell": str(gateio_route_exposure),
        "classification": "exchange_route_exposure_not_excluded",
        "notes": "Not excluded from circulating supply; this is route exposure, not locked supply.",
    },
]

with open("circulating_supply_estimate.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["metric", "amount_cell", "classification", "notes"])
    w.writeheader()
    w.writerows(rows)

print("==============================")
print("CIRCULATING SUPPLY ESTIMATE")
print("==============================")
print(f"ETH totalSupply:                         {eth_total:,.8f} CELL")
print(f"BSC totalSupply:                         {bsc_total:,.8f} CELL")
print(f"Raw ETH+BSC contract supply:             {raw_total:,.8f} CELL")
print(f"Verified backing/reserve candidates:     {conservative_non_circulating:,.8f} CELL")
print()
print(f"Conservative circulating estimate:       {conservative_circulating_estimate:,.8f} CELL")
print(f"BSC conservative circulating estimate:   {bsc_conservative_circulating_estimate:,.8f} CELL")
print(f"BSC supply minus ETH backing candidates: {bsc_unbacked_or_unreconciled:,.8f} CELL")
print()
print("Saved:")
print("- circulating_supply_estimate.json")
print("- circulating_supply_estimate.csv")
