import csv
import json
import os
import subprocess
from pathlib import Path

CHILDREN = [
    ("0x2b3965bf98941fcf182be5a054b31ce97dff3575", 93989480),
    ("0xcacdbc3f50b73ce847379865e6dc9fee3026d013", 93989480),
    ("0x9d50c34e1a1fd8bea6b02aeb33c9dc7b40a4217a", 93989480),
    ("0x3c479060afe2ddfa2c873bb5c9c00b5458b8adbc", 93989480),
    ("0x838bf83b33d18bc377997b4c0293afb6c99a5b50", 93989480),
    ("0xaeb5b7ee8231019b3443bf546aa38eaf4937cf51", 93989480),
    ("0xe1de032a7e99ed3cc6ca02b70ca760b50cb46337", 93989480),
    ("0xd52f8fca137f5974d68bf4c79cb8aea1ee3d127e", 93989480),
    ("0x68d350de0a4e35be14eba5542ec823a3f13168d4", 93989480),
    ("0x3d1c85c85c54a0f6fd2d6da2d15dc80c86babca7", 93989480),
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
    env["MAX_TRACE_CHANGES"] = "100"

    result = subprocess.run(["python3", "auto_trace_bsc_wallet.py"], env=env)

    generic_events = Path("auto_trace_wallet_events.csv")
    generic_summary = Path("auto_trace_wallet_summary.json")

    out_events = Path(f"auto_trace_oldcell_child_{short}_events.csv")
    out_summary = Path(f"auto_trace_oldcell_child_{short}_summary.json")

    if generic_events.exists():
        generic_events.replace(out_events)
    if generic_summary.exists():
        generic_summary.replace(out_summary)

    if out_summary.exists():
        data = json.loads(out_summary.read_text())
        summary_rows.append({
            "wallet": wallet,
            "events_file": str(out_events),
            "summary_file": str(out_summary),
            "current_balance_cell": data.get("current_balance_cell"),
            "change_count": data.get("change_count"),
            "event_count": data.get("event_count"),
            "latest_processed_block": data.get("latest_processed_block"),
        })

with open("oldcell_458b_child_probe_summary.csv", "w", newline="") as f:
    fields = [
        "wallet",
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

Path("oldcell_458b_child_probe_summary.json").write_text(json.dumps(summary_rows, indent=2))

print("\nSaved:")
print("- oldcell_458b_child_probe_summary.csv")
print("- oldcell_458b_child_probe_summary.json")
