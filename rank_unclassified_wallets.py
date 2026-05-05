import csv
from pathlib import Path

INFILE = Path("bridge_cluster_unclassified_wallets.csv")
OUTFILE = Path("wallet_label_priority_review.csv")

def fnum(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def classify_hint(row):
    incoming = fnum(row.get("incoming_cell_all_dataset"))
    outgoing = fnum(row.get("outgoing_cell_all_dataset"))
    net = fnum(row.get("net_cell_all_dataset"))
    out_edges = int(fnum(row.get("outgoing_edges")))

    total = incoming + outgoing
    pass_through_ratio = min(incoming, outgoing) / max(incoming, outgoing) if max(incoming, outgoing) else 0

    if total >= 5_000_000 and pass_through_ratio > 0.90 and out_edges > 50:
        return "likely router / exchange / aggregator"
    if outgoing >= 1_000_000 and out_edges > 100:
        return "likely distributor / router"
    if incoming >= 1_000_000 and outgoing < incoming * 0.10:
        return "possible custody / holder"
    if incoming >= 1_000_000 and outgoing >= incoming * 0.80:
        return "pass-through wallet"
    if out_edges >= 50:
        return "high-activity routing wallet"
    if abs(net) < total * 0.05 and total >= 100_000:
        return "balanced pass-through"
    return "manual review"

if not INFILE.exists():
    raise FileNotFoundError("Missing bridge_cluster_unclassified_wallets.csv. Run trace_bridge_cluster.py first.")

rows = []
with INFILE.open(newline="") as f:
    for r in csv.DictReader(f):
        incoming = fnum(r.get("incoming_cell_all_dataset"))
        outgoing = fnum(r.get("outgoing_cell_all_dataset"))
        net = fnum(r.get("net_cell_all_dataset"))
        volume = incoming + outgoing

        r["total_volume_cell"] = volume
        r["classification_hint"] = classify_hint(r)

        # Preserve existing manual labels if already present.
        r.setdefault("manual_label", "")
        r.setdefault("manual_class", "")
        r.setdefault("notes", "")
        rows.append(r)

rows.sort(key=lambda r: fnum(r["total_volume_cell"]), reverse=True)

fields = [
    "address",
    "address_short",
    "first_seen_hop",
    "incoming_cell_all_dataset",
    "outgoing_cell_all_dataset",
    "net_cell_all_dataset",
    "total_volume_cell",
    "incoming_edges",
    "outgoing_edges",
    "suggested_review",
    "classification_hint",
    "manual_label",
    "manual_class",
    "notes",
]

with OUTFILE.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

print(f"Saved {OUTFILE}")
print("\nTop 30 wallets to label:")
for r in rows[:30]:
    print(
        f"{fnum(r['total_volume_cell']):,.2f} volume | "
        f"in={fnum(r['incoming_cell_all_dataset']):,.2f} | "
        f"out={fnum(r['outgoing_cell_all_dataset']):,.2f} | "
        f"hop={r['first_seen_hop']} | "
        f"{r['address']} | {r['classification_hint']}"
    )
