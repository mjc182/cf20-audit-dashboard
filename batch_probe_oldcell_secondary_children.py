import csv
import json
import os
import subprocess
from pathlib import Path

CHILDREN = [
    ("0x83492406ec56b85d1840b708b66255a2c15ef458", 94055014),
    ("0x03e2b199dc23f271007ce68ba26549130d103028", 94056661),
    ("0x21baf7475329d17434a0827ad1e5968ed441bc1f", 94161924),
    ("0x3cb0dd3dd55f32f94fc87992788e7196f563ac54", 94162074),
]

TOKEN = "0xf3e1449ddb6b218da2c9463d4594ceccc8934346"
END_BLOCK = os.environ.get("OLD_CELL_CHILD_END_BLOCK", "96716000")

summary_rows = []

for i, (wallet, start_block) in enumerate(CHILDREN, 1):
    short = wallet[2:6]
    print("=" * 30)
    print(f"[{i}/{len(CHILDREN)}] probing {wallet}")
    print("=" * 30)

    env = os.environ.copy()
    env["BSC_CELL_TOKEN"] = TOKEN
    env["TARGET_WALLET"] = wallet
    env["BSC_START_BLOCK"] = str(start_block + 1)
    env["BSC_END_BLOCK"] = END_BLOCK
    env["BALANCE_PROBE_STEP"] = "1000"
    env["LOG_CHUNK_SIZE"] = "10"
    env["MAX_TRACE_CHANGES"] = "500"

    subprocess.run(["python3", "auto_trace_bsc_wallet.py"], env=env)

    generic_events = Path("auto_trace_wallet_events.csv")
    generic_summary = Path("auto_trace_wallet_summary.json")

    out_events = Path(f"auto_trace_oldcell_secondary_{short}_events.csv")
    out_summary = Path(f"auto_trace_oldcell_secondary_{short}_summary.json")

    if generic_events.exists():
        generic_events.replace(out_events)
    if generic_summary.exists():
        generic_summary.replace(out_summary)

    if out_summary.exists():
        data = json.loads(out_summary.read_text())
        summary_rows.append({
            "wallet": wallet,
            "start_block": start_block,
            "current_balance_cell": data.get("current_balance_cell"),
            "change_count": data.get("change_count"),
            "event_count": data.get("event_count"),
            "latest_processed_block": data.get("latest_processed_block"),
            "events_file": str(out_events),
            "summary_file": str(out_summary),
        })

with open("oldcell_secondary_child_probe_summary.csv", "w", newline="") as f:
    fields = [
        "wallet",
        "start_block",
        "current_balance_cell",
        "change_count",
        "event_count",
        "latest_processed_block",
        "events_file",
        "summary_file",
    ]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(summary_rows)

Path("oldcell_secondary_child_probe_summary.json").write_text(json.dumps(summary_rows, indent=2))

print("\nSaved:")
print("- oldcell_secondary_child_probe_summary.csv")
print("- oldcell_secondary_child_probe_summary.json")
