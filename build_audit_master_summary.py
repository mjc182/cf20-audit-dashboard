import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CELL_PER_MCELL = 1000

OFFICIAL_ILLEGAL_MCELL = 1295
OFFICIAL_CELL_EQUIV = OFFICIAL_ILLEGAL_MCELL * CELL_PER_MCELL

ETH_CELL_TOKEN = "0x26c8afbbfe1ebaca03c2bb082e69d0476bffe099"
BSC_CELL_TOKEN = "0xd98438889Ae7364c7E2A3540547Fad042FB24642"

# Evidence files produced by the existing scripts
MISSING_EVENTS = Path("missing_cell_events.csv")
MISSING_WALLETS = Path("missing_cell_wallets.csv")
MISSING_SUMMARY = Path("missing_cell_summary.json")
CROSSCHECK = Path("cf20_mint_crosscheck.csv")
CROSSCHECK_SUMMARY = Path("cf20_mint_crosscheck_summary.json")
OUTFLOW_RAW = Path("zerochain_missing_cell_activity_raw.csv")
OUTFLOW_SUMMARY = Path("zerochain_missing_cell_outflow_summary.csv")
VERIFIED_WALLETS = Path("verified_wallets.json")
VERIFIED_BALANCES = Path("verified_wallet_balances.json")

# New normalized / audit-grade outputs
OUT_MASTER = Path("audit_master_summary.json")
OUT_EVENTS_DEDUPED = Path("missing_cell_events_deduped.csv")
OUT_WALLETS_DEDUPED = Path("missing_cell_wallets_deduped.csv")
OUT_HASHES_JSON = Path("evidence_hashes.json")
OUT_HASHES_CSV = Path("evidence_hashes.csv")

TARGET_TOKENS = {"CELL", "mCELL", "CF20"}

# Manual bridge-out evidence from the DATUM_TX JSON you found.
# Keep this here so the dashboard can show the bridge-out evidence even before BSC-side sale tracing is complete.
MANUAL_BRIDGE_OUT_EVIDENCE = {
    "found": True,
    "source_wallet_short": "Rj7J7...MLE7o7T",
    "source_wallet": "Rj7J7MiX2bWy8sNyXN6YqRfWnuX8VkcRfBF2uzuAgC5fZ5UiL5thQxX6rNyRMaCBvBWLVN8xjkmgs7VVSvqnNE3BKVXV6xTvYMLE7o7T",
    "datum_type": "DATUM_TX",
    "transaction_hash": "0x03F5934B41AE409E81258BD7C7FA55B86A52CA829D413E0D791E2A0D96E8E9A4",
    "atom_hash": "0xFF141C49A63FD7D2B69B2EC2E4835923584FFFF73E8F7F8E2CDB3D52C3C01717",
    "created_at": "2026-04-13T11:31:24",
    "service_name": "bridge",
    "action": "close",
    "direction_tag": "OUT",
    "destination_chain_type": "BEP20",
    "bep20_destination": "0x1fa6348d9b13d316c62d54f62bea4e1a7207d9d6",
    "bridge_condition_value_raw": "3876436277458157528389260",
    "bridge_condition_value_cell": 3876436.2774581575,
    "sale_quantified": False,
    "sale_status": "Bridge-out route identified; BSC/DEX/OTC sale path not yet quantified.",
}


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def to_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def read_csv(path):
    if not path.exists():
        return []

    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_json(path, default):
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def sha256_file(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def dedupe_events(rows):
    """
    Deduplicate CELL/mCELL unmatched events.

    Primary key: datum_hash.
    Fallback key: mint_time + mint_to + token + amount.
    """
    seen = set()
    deduped = []
    duplicates = []

    for row in rows:
        token = (row.get("token") or "").strip()

        if token and token not in TARGET_TOKENS:
            continue

        match_status = row.get("match_status", "unmatched")
        if match_status and match_status != "unmatched":
            continue

        datum_hash = (row.get("datum_hash") or "").strip()

        if datum_hash:
            key = ("datum_hash", datum_hash)
        else:
            key = (
                "fallback",
                row.get("mint_time", ""),
                row.get("mint_to", ""),
                token,
                str(row.get("mint_amount_tokens", "")),
            )

        if key in seen:
            duplicates.append(row)
            continue

        seen.add(key)

        amount = to_float(row.get("mint_amount_tokens"))
        row["mint_amount_tokens"] = amount
        row["mint_amount_mcell_equivalent"] = amount / CELL_PER_MCELL
        deduped.append(row)

    deduped.sort(key=lambda r: to_float(r.get("mint_amount_tokens")), reverse=True)
    return deduped, duplicates


def wallet_summary_from_events(events):
    wallets = defaultdict(lambda: {
        "mint_to": "",
        "missing_cell": 0.0,
        "missing_mcell_equivalent": 0.0,
        "share_of_missing": 0.0,
        "events": 0,
        "first_seen": "",
        "last_seen": "",
        "max_single_mint": 0.0,
        "top_datum_hashes": [],
    })

    for row in events:
        wallet = row.get("mint_to") or "unknown"
        amount = to_float(row.get("mint_amount_tokens"))
        t = row.get("mint_time", "")
        datum_hash = row.get("datum_hash", "")

        w = wallets[wallet]
        w["mint_to"] = wallet
        w["missing_cell"] += amount
        w["missing_mcell_equivalent"] += amount / CELL_PER_MCELL
        w["events"] += 1
        w["max_single_mint"] = max(w["max_single_mint"], amount)

        if not w["first_seen"] or t < w["first_seen"]:
            w["first_seen"] = t

        if not w["last_seen"] or t > w["last_seen"]:
            w["last_seen"] = t

        if datum_hash and len(w["top_datum_hashes"]) < 5:
            w["top_datum_hashes"].append(datum_hash)

    total = sum(w["missing_cell"] for w in wallets.values())

    rows = []
    for w in wallets.values():
        w["share_of_missing"] = (w["missing_cell"] / total * 100) if total else 0
        w["top_datum_hashes"] = ", ".join(w["top_datum_hashes"])
        rows.append(dict(w))

    rows.sort(key=lambda r: r["missing_cell"], reverse=True)
    return rows


def build_hash_manifest():
    files = [
        MISSING_EVENTS,
        MISSING_WALLETS,
        MISSING_SUMMARY,
        CROSSCHECK,
        CROSSCHECK_SUMMARY,
        OUTFLOW_RAW,
        OUTFLOW_SUMMARY,
        VERIFIED_WALLETS,
        VERIFIED_BALANCES,
        OUT_EVENTS_DEDUPED,
        OUT_WALLETS_DEDUPED,
        OUT_MASTER,
    ]

    rows = []

    for path in files:
        if not path.exists():
            rows.append({
                "file": str(path),
                "exists": False,
                "size_bytes": 0,
                "sha256": "",
            })
            continue

        rows.append({
            "file": str(path),
            "exists": True,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })

    return rows


def main():
    print("\n==============================")
    print("CF20 AUDIT MASTER SUMMARY BUILDER")
    print("==============================\n")

    missing_events = read_csv(MISSING_EVENTS)

    if not missing_events:
        raise FileNotFoundError(
            "missing_cell_events.csv is missing or empty. "
            "Run filter_missing_cell_only.py first."
        )

    deduped_events, duplicate_events = dedupe_events(missing_events)
    wallet_rows = wallet_summary_from_events(deduped_events)

    event_fieldnames = list(deduped_events[0].keys()) if deduped_events else [
        "mint_time",
        "token",
        "mint_amount_tokens",
        "mint_amount_mcell_equivalent",
        "mint_to",
        "datum_hash",
        "atom_hash",
        "validator_count",
        "match_status",
        "candidate_count",
    ]

    wallet_fieldnames = [
        "mint_to",
        "missing_cell",
        "missing_mcell_equivalent",
        "share_of_missing",
        "events",
        "first_seen",
        "last_seen",
        "max_single_mint",
        "top_datum_hashes",
    ]

    write_csv(OUT_EVENTS_DEDUPED, deduped_events, event_fieldnames)
    write_csv(OUT_WALLETS_DEDUPED, wallet_rows, wallet_fieldnames)

    deduped_missing_cell = sum(to_float(r.get("mint_amount_tokens")) for r in deduped_events)
    deduped_missing_mcell = deduped_missing_cell / CELL_PER_MCELL

    top5_cell = sum(to_float(r.get("missing_cell")) for r in wallet_rows[:5])
    top5_share = (top5_cell / deduped_missing_cell * 100) if deduped_missing_cell else 0

    largest_wallet = wallet_rows[0] if wallet_rows else {}

    cross_summary = read_json(CROSSCHECK_SUMMARY, {})
    original_missing_summary = read_json(MISSING_SUMMARY, {})
    outflow_summary = read_json(Path("zerochain_missing_cell_outflow_summary.json"), {})

    master = {
        "generated_at_utc": now_utc(),
        "unit_conversion": {
            "cell_per_mcell": CELL_PER_MCELL,
            "statement": "1 mCELL = 1,000 CELL",
        },
        "contracts": {
            "eth_cell_token": ETH_CELL_TOKEN,
            "bsc_cell_token": BSC_CELL_TOKEN,
        },
        "official_disclosure": {
            "illegal_mcell": OFFICIAL_ILLEGAL_MCELL,
            "cell_equivalent": OFFICIAL_CELL_EQUIV,
            "note": "Official Cellframe statement figure converted using 1 mCELL = 1,000 CELL.",
        },
        "independent_chain_analysis": {
            "deduped_unmatched_cell": deduped_missing_cell,
            "deduped_unmatched_mcell_equivalent": deduped_missing_mcell,
            "original_missing_summary": original_missing_summary,
            "event_count_deduped": len(deduped_events),
            "event_duplicates_removed": len(duplicate_events),
            "recipient_count_deduped": len(wallet_rows),
            "top5_missing_cell": top5_cell,
            "top5_share_percent": top5_share,
            "largest_wallet": largest_wallet,
        },
        "matching_summary": cross_summary,
        "bridge_out_evidence": MANUAL_BRIDGE_OUT_EVIDENCE,
        "outflow_trace_summary": outflow_summary,
        "market_sale_quantification": {
            "status": "unresolved",
            "proven_sold_amount_cell": None,
            "note": "Bridge-out evidence exists, but BSC/DEX/OTC sale route has not been quantified yet.",
        },
        "confidence": {
            "unmatched_emissions": "high",
            "deduped_top_wallet_concentration": "high",
            "bridge_out_link": "high",
            "scheme_participant_wallet_classification": "medium",
            "open_market_sale_amount": "unresolved",
        },
        "methodology": {
            "deduplication_key": "datum_hash, fallback mint_time+mint_to+token+amount",
            "target_tokens": sorted(TARGET_TOKENS),
            "important_limitations": [
                "Known wallet matching may be incomplete.",
                "Emission records prove receipt, not sale.",
                "Bridge-out transaction proves external-chain exit route, not final market sale.",
                "BSC/DEX/OTC tracing remains pending for exact sold amount.",
                "Official disclosure figure and independent unmatched-emission figure are not assumed to be identical.",
            ],
        },
        "outputs": {
            "deduped_events_csv": str(OUT_EVENTS_DEDUPED),
            "deduped_wallets_csv": str(OUT_WALLETS_DEDUPED),
            "master_summary_json": str(OUT_MASTER),
            "evidence_hashes_json": str(OUT_HASHES_JSON),
            "evidence_hashes_csv": str(OUT_HASHES_CSV),
        },
    }

    OUT_MASTER.write_text(json.dumps(master, indent=2))

    hash_rows = build_hash_manifest()
    OUT_HASHES_JSON.write_text(json.dumps(hash_rows, indent=2))
    write_csv(OUT_HASHES_CSV, hash_rows, ["file", "exists", "size_bytes", "sha256"])

    print("Master summary created.")
    print(f"Deduped missing CELL:            {deduped_missing_cell:,.2f}")
    print(f"Deduped mCELL equivalent:        {deduped_missing_mcell:,.2f}")
    print(f"Duplicate events removed:        {len(duplicate_events):,}")
    print(f"Recipient wallets deduped:       {len(wallet_rows):,}")
    print(f"Top 5 share:                     {top5_share:,.2f}%")
    print(f"Official mCELL disclosure:       {OFFICIAL_ILLEGAL_MCELL:,.0f} mCELL")
    print(f"Official CELL-equivalent:        {OFFICIAL_CELL_EQUIV:,.2f} CELL")

    print("\nSaved:")
    print(f"- {OUT_MASTER}")
    print(f"- {OUT_EVENTS_DEDUPED}")
    print(f"- {OUT_WALLETS_DEDUPED}")
    print(f"- {OUT_HASHES_JSON}")
    print(f"- {OUT_HASHES_CSV}")


if __name__ == "__main__":
    main()
