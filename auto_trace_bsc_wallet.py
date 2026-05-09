#!/usr/bin/env python3
"""
Auto-trace BSC CELL balance changes for one wallet.

Designed for the 0xc3b8... BSC custody wallet.

Outputs:
- auto_trace_wallet_events.csv
- auto_trace_wallet_summary.json

Usage:
export BSC_RPC="https://bnb-mainnet.g.alchemy.com/v2/7fMZOoLaR5Kjh5UZn0LC4"
export TARGET_WALLET="0xc3b8a652e59d59a71b00808c1fb2432857080ab8"
export BSC_START_BLOCK=34655452
export BSC_END_BLOCK=96716000
export BALANCE_PROBE_STEP=10000
export LOG_CHUNK_SIZE=10

python3 auto_trace_bsc_wallet.py
"""

import csv
import json
import os
import time
import urllib.error
import urllib.request
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 80

RPC = os.getenv("BSC_RPC", "").strip()
TOKEN = os.getenv("BSC_CELL_TOKEN", "0xd98438889ae7364c7e2a3540547fad042fb24642").lower()
TARGET = os.getenv("TARGET_WALLET", "0xc3b8a652e59d59a71b00808c1fb2432857080ab8").lower()

START_BLOCK = int(os.getenv("BSC_START_BLOCK", "34655452"))
END_BLOCK_ENV = os.getenv("BSC_END_BLOCK", "").strip()
PROBE_STEP = int(os.getenv("BALANCE_PROBE_STEP", "10000"))
LOG_CHUNK_SIZE = int(os.getenv("LOG_CHUNK_SIZE", "10"))

OUT_EVENTS = Path("auto_trace_wallet_events.csv")
OUT_SUMMARY = Path("auto_trace_wallet_summary.json")

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BALANCE_OF_SELECTOR = "0x70a08231"
DECIMALS = 18

if not RPC:
    raise SystemExit("Set BSC_RPC first.")


def rpc_call(method, params, retries=3):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }).encode("utf-8")

    req = urllib.request.Request(
        RPC,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_error = None

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if "error" in data:
                raise RuntimeError(data["error"])

            return data["result"]

        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            last_error = RuntimeError(f"HTTP {e.code} {e.reason}: {body}")
            time.sleep(0.4 * (attempt + 1))

        except Exception as e:
            last_error = e
            time.sleep(0.4 * (attempt + 1))

    raise last_error


def latest_block():
    return int(rpc_call("eth_blockNumber", []), 16)


def pad_addr(addr):
    return addr.lower().replace("0x", "").rjust(64, "0")


def topic_address(addr):
    return "0x" + addr.lower().replace("0x", "").rjust(64, "0")


def topic_to_address(topic):
    return "0x" + topic[-40:].lower()


def decode_uint(x):
    if not x or x == "0x":
        return 0
    return int(x, 16)


def cell(raw):
    return Decimal(raw) / Decimal(10 ** DECIMALS)


def balance_raw(block):
    data = BALANCE_OF_SELECTOR + pad_addr(TARGET)
    result = rpc_call("eth_call", [{"to": TOKEN, "data": data}, hex(block)])
    return decode_uint(result)


def get_logs(from_block, to_block, topics):
    params = {
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
        "address": TOKEN,
        "topics": topics,
    }
    return rpc_call("eth_getLogs", [params])


def get_logs_chunked(from_block, to_block, topics):
    logs = []
    current = from_block

    while current <= to_block:
        end = min(current + LOG_CHUNK_SIZE - 1, to_block)
        try:
            part = get_logs(current, end, topics)
            logs.extend(part)
        except Exception as e:
            print(f"Log error {current:,}->{end:,}: {e}")
        current = end + 1

    return logs


def parse_log(log, direction):
    topics = log.get("topics", [])
    from_addr = topic_to_address(topics[1]) if len(topics) > 1 else ""
    to_addr = topic_to_address(topics[2]) if len(topics) > 2 else ""
    raw = decode_uint(log.get("data", "0x0"))

    return {
        "chain": "bsc",
        "token": TOKEN,
        "target_wallet": TARGET,
        "direction": direction,
        "block_number": int(log["blockNumber"], 16),
        "tx_hash": log.get("transactionHash", ""),
        "log_index": int(log.get("logIndex", "0x0"), 16),
        "from": from_addr,
        "to": to_addr,
        "amount_raw": str(raw),
        "amount_cell": str(cell(raw)),
    }


def find_first_change(start_block, end_block, start_balance):
    """
    Probe forward by PROBE_STEP until balance != start_balance.
    Then binary-search the exact first changed block.
    """
    previous = start_block
    probe = start_block + PROBE_STEP

    while probe <= end_block:
        b = balance_raw(probe)

        if b != start_balance:
            lo, hi = previous, probe
            first = None

            while lo <= hi:
                mid = (lo + hi) // 2
                mb = balance_raw(mid)

                if mb != start_balance:
                    first = mid
                    hi = mid - 1
                else:
                    lo = mid + 1

            return first

        previous = probe
        probe += PROBE_STEP

    # Final short range check.
    if previous < end_block:
        b = balance_raw(end_block)
        if b != start_balance:
            lo, hi = previous, end_block
            first = None

            while lo <= hi:
                mid = (lo + hi) // 2
                mb = balance_raw(mid)

                if mb != start_balance:
                    first = mid
                    hi = mid - 1
                else:
                    lo = mid + 1

            return first

    return None


def collect_target_logs_around(block):
    """
    Pull inbound and outbound Transfer logs involving TARGET around the changed block.
    """
    start = max(block - 20, 0)
    end = block + 20

    out_topics = [
        TRANSFER_TOPIC,
        topic_address(TARGET),
        None,
    ]

    in_topics = [
        TRANSFER_TOPIC,
        None,
        topic_address(TARGET),
    ]

    out_logs = get_logs_chunked(start, end, out_topics)
    in_logs = get_logs_chunked(start, end, in_topics)

    rows = []

    seen = set()

    for log in out_logs:
        key = (log.get("transactionHash"), log.get("logIndex"), "out")
        if key not in seen:
            seen.add(key)
            rows.append(parse_log(log, "out"))

    for log in in_logs:
        key = (log.get("transactionHash"), log.get("logIndex"), "in")
        if key not in seen:
            seen.add(key)
            rows.append(parse_log(log, "in"))

    rows.sort(key=lambda r: (r["block_number"], r["log_index"], r["direction"]))
    return rows


def write_outputs(events, summary):
    fields = [
        "chain",
        "token",
        "target_wallet",
        "direction",
        "block_number",
        "tx_hash",
        "log_index",
        "from",
        "to",
        "amount_raw",
        "amount_cell",
        "balance_before_cell",
        "balance_after_cell",
    ]

    with OUT_EVENTS.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for e in events:
            writer.writerow({k: e.get(k, "") for k in fields})

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2))


def main():
    end_block = int(END_BLOCK_ENV) if END_BLOCK_ENV else latest_block()

    print("==============================")
    print("AUTO TRACE BSC CELL WALLET")
    print("==============================")
    print(f"Token:       {TOKEN}")
    print(f"Target:      {TARGET}")
    print(f"Start block: {START_BLOCK:,}")
    print(f"End block:   {end_block:,}")
    print(f"Probe step:  {PROBE_STEP:,}")
    print(f"Log chunk:   {LOG_CHUNK_SIZE:,}")

    current_block = START_BLOCK
    current_balance = balance_raw(current_block)

    print(f"Start balance: {cell(current_balance):,.8f} CELL")

    events = []
    changes = []

    max_iterations = int(os.getenv("MAX_TRACE_CHANGES", "200"))

    for i in range(max_iterations):
        if current_block >= end_block:
            print("Reached end block.")
            break

        if current_balance == 0:
            print("Balance is zero. Trace complete.")
            break

        print(f"\nSearching for change after block {current_block:,} with balance {cell(current_balance):,.8f} CELL...")

        changed_block = find_first_change(current_block, end_block, current_balance)

        if changed_block is None:
            print("No further balance change found before end block.")
            break

        before = balance_raw(changed_block - 1)
        after = balance_raw(changed_block)

        delta = Decimal(after - before) / Decimal(10 ** DECIMALS)

        print("==============================")
        print(f"Change #{i + 1}")
        print(f"Block:          {changed_block:,}")
        print(f"Balance before: {cell(before):,.8f} CELL")
        print(f"Balance after:  {cell(after):,.8f} CELL")
        print(f"Delta:          {delta:,.8f} CELL")

        rows = collect_target_logs_around(changed_block)

        if not rows:
            print("No target transfer logs found around this block.")
        else:
            print("Transfer logs around change:")
            for r in rows:
                print(
                    f"{r['direction'].upper()} | block={r['block_number']} | "
                    f"{Decimal(r['amount_cell']):,.8f} CELL | "
                    f"from={r['from']} | to={r['to']} | tx={r['tx_hash']}"
                )

        for r in rows:
            r["balance_before_cell"] = str(cell(before))
            r["balance_after_cell"] = str(cell(after))
            events.append(r)

        changes.append({
            "change_number": i + 1,
            "block_number": changed_block,
            "balance_before_raw": str(before),
            "balance_before_cell": str(cell(before)),
            "balance_after_raw": str(after),
            "balance_after_cell": str(cell(after)),
            "delta_cell": str(delta),
            "logs_found": len(rows),
        })

        current_block = changed_block
        current_balance = after

        summary = {
            "chain": "bsc",
            "token": TOKEN,
            "target_wallet": TARGET,
            "start_block": START_BLOCK,
            "end_block": end_block,
            "latest_processed_block": current_block,
            "current_balance_cell": str(cell(current_balance)),
            "change_count": len(changes),
            "event_count": len(events),
            "changes": changes,
            "note": "Auto trace uses balance probes plus Transfer logs around each detected change.",
        }

        write_outputs(events, summary)

        # Move one block forward for next search. Balance at current_block is after all txs in that block.
        current_block = changed_block + 1
        current_balance = balance_raw(current_block)

    summary = {
        "chain": "bsc",
        "token": TOKEN,
        "target_wallet": TARGET,
        "start_block": START_BLOCK,
        "end_block": end_block,
        "latest_processed_block": current_block,
        "current_balance_cell": str(cell(current_balance)),
        "change_count": len(changes),
        "event_count": len(events),
        "changes": changes,
        "note": "Auto trace uses balance probes plus Transfer logs around each detected change.",
    }

    write_outputs(events, summary)

    print("\n==============================")
    print("AUTO TRACE COMPLETE")
    print("==============================")
    print(f"Changes found:          {len(changes):,}")
    print(f"Transfer events saved:  {len(events):,}")
    print(f"Current balance:        {cell(current_balance):,.8f} CELL")
    print("\nSaved:")
    print(f"- {OUT_EVENTS}")
    print(f"- {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
