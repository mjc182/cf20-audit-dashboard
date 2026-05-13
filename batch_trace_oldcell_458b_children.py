import csv
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

RPC = os.environ["BSC_RPC"]
TOKEN = "0xf3e1449ddb6b218da2c9463d4594ceccc8934346"
START_BLOCK = int(os.getenv("OLD_CELL_CHILD_START_BLOCK", "93989480"))
END_BLOCK = int(os.getenv("OLD_CELL_CHILD_END_BLOCK", "96716000"))
CHUNK = int(os.getenv("LOG_CHUNK_SIZE", "10"))

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BALANCE_OF_SELECTOR = "0x70a08231"

CHILDREN = [
    "0x2b3965bf98941fcf182be5a054b31ce97dff3575",
    "0xcacdbc3f50b73ce847379865e6dc9fee3026d013",
    "0x9d50c34e1a1fd8bea6b02aeb33c9dc7b40a4217a",
    "0x3c479060afe2ddfa2c873bb5c9c00b5458b8adbc",
    "0x838bf83b33d18bc377997b4c0293afb6c99a5b50",
    "0xaeb5b7ee8231019b3443bf546aa38eaf4937cf51",
    "0xe1de032a7e99ed3cc6ca02b70ca760b50cb46337",
    "0xd52f8fca137f5974d68bf4c79cb8aea1ee3d127e",
    "0x68d350de0a4e35be14eba5542ec823a3f13168d4",
    "0x3d1c85c85c54a0f6fd2d6da2d15dc80c86babca7",
]

# Known labels we should flag conservatively.
KNOWN_EXCHANGE_OR_ROUTER = {
    "0x3cc936b795a188f0e246cbb2d74c5bd190aecf18": "MEXC 3 / exchange-labelled",
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Gate.io 1 / exchange-labelled",
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap Universal Router",
    "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch Router",
}

def rpc_call(method, params, retries=4):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }).encode()

    req = urllib.request.Request(
        RPC,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            if "error" in data:
                raise RuntimeError(data["error"])
            return data["result"]
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            last = RuntimeError(f"HTTP {e.code}: {body}")
            time.sleep(0.5 * (attempt + 1))
        except Exception as e:
            last = e
            time.sleep(0.5 * (attempt + 1))
    raise last

def topic_addr(addr):
    return "0x" + addr.lower().replace("0x", "").rjust(64, "0")

def addr_from_topic(topic):
    return "0x" + topic[-40:].lower()

def amount(data):
    return Decimal(int(data, 16)) / Decimal(10 ** 18)

def pad_addr(addr):
    return addr.lower().replace("0x", "").rjust(64, "0")

def balance_at(addr, block="latest"):
    data = BALANCE_OF_SELECTOR + pad_addr(addr)
    result = rpc_call("eth_call", [{"to": TOKEN, "data": data}, block if block == "latest" else hex(block)])
    return Decimal(int(result, 16)) / Decimal(10 ** 18)

def get_logs(start, end, topics):
    return rpc_call("eth_getLogs", [{
        "fromBlock": hex(start),
        "toBlock": hex(end),
        "address": TOKEN,
        "topics": topics,
    }])

def scan_wallet_outbound(wallet):
    logs = []
    current = START_BLOCK
    while current <= END_BLOCK:
        stop = min(current + CHUNK - 1, END_BLOCK)
        try:
            part = get_logs(current, stop, [TRANSFER_TOPIC, topic_addr(wallet), None])
            logs.extend(part)
        except Exception as e:
            print(f"error wallet={wallet} blocks={current}->{stop}: {e}")
        current = stop + 1
    return logs

all_events = []
summary_rows = []

print("==============================")
print("OLD CELL 0x458b CHILD WALLET BATCH TRACE")
print("==============================")
print(f"Token:       {TOKEN}")
print(f"Start block: {START_BLOCK:,}")
print(f"End block:   {END_BLOCK:,}")
print(f"Chunk size:  {CHUNK}")
print()

for i, wallet in enumerate(CHILDREN, 1):
    print(f"[{i}/{len(CHILDREN)}] scanning {wallet}")

    outbound_logs = scan_wallet_outbound(wallet)
    latest_bal = balance_at(wallet, "latest")

    out_total = Decimal("0")
    recipients = defaultdict(Decimal)
    tx_count = 0
    exchange_hits = []

    for log in outbound_logs:
        topics = log["topics"]
        from_addr = addr_from_topic(topics[1])
        to_addr = addr_from_topic(topics[2])
        amt = amount(log["data"])
        out_total += amt
        recipients[to_addr] += amt
        tx_count += 1

        label = KNOWN_EXCHANGE_OR_ROUTER.get(to_addr.lower(), "")
        if label:
            exchange_hits.append({
                "to": to_addr,
                "label": label,
                "amount_cell_old": str(amt),
                "tx_hash": log["transactionHash"],
                "block_number": int(log["blockNumber"], 16),
            })

        all_events.append({
            "source_child_wallet": wallet,
            "block_number": int(log["blockNumber"], 16),
            "tx_hash": log["transactionHash"],
            "log_index": int(log["logIndex"], 16),
            "from": from_addr,
            "to": to_addr,
            "amount_cell_old": str(amt),
            "known_label": label,
        })

    top_to = ""
    top_amt = Decimal("0")
    if recipients:
        top_to, top_amt = sorted(recipients.items(), key=lambda x: x[1], reverse=True)[0]

    status = "held_no_outbound" if tx_count == 0 and latest_bal > 0 else "routed_onward" if tx_count else "empty_no_outbound_found"
    if exchange_hits:
        status = "exchange_or_router_hit"

    summary_rows.append({
        "wallet": wallet,
        "latest_balance_cell_old": str(latest_bal),
        "outbound_total_cell_old": str(out_total),
        "outbound_txs": tx_count,
        "unique_recipients": len(recipients),
        "top_recipient": top_to,
        "top_recipient_amount_cell_old": str(top_amt),
        "status": status,
        "known_exchange_or_router_hits": json.dumps(exchange_hits),
    })

    print(f"  latest balance: {latest_bal:,.8f} CELL-old")
    print(f"  outbound total: {out_total:,.8f} CELL-old")
    print(f"  outbound txs:   {tx_count}")
    if top_to:
        print(f"  top recipient:  {top_amt:,.8f} -> {top_to}")
    if exchange_hits:
        print("  !!! known exchange/router hit:")
        for h in exchange_hits:
            print(f"    {h['amount_cell_old']} -> {h['to']} ({h['label']}) tx={h['tx_hash']}")
    print()

with open("oldcell_458b_child_wallet_events.csv", "w", newline="") as f:
    fields = [
        "source_child_wallet",
        "block_number",
        "tx_hash",
        "log_index",
        "from",
        "to",
        "amount_cell_old",
        "known_label",
    ]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(sorted(all_events, key=lambda r: (r["source_child_wallet"], r["block_number"], r["log_index"])))

with open("oldcell_458b_child_wallet_summary.csv", "w", newline="") as f:
    fields = [
        "wallet",
        "latest_balance_cell_old",
        "outbound_total_cell_old",
        "outbound_txs",
        "unique_recipients",
        "top_recipient",
        "top_recipient_amount_cell_old",
        "status",
        "known_exchange_or_router_hits",
    ]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(summary_rows)

result = {
    "token": TOKEN,
    "start_block": START_BLOCK,
    "end_block": END_BLOCK,
    "children_scanned": len(CHILDREN),
    "event_count": len(all_events),
    "summary": summary_rows,
    "audit_interpretation": (
        "Batch trace of the ten 100k old-CELL child wallets from 0x458b. "
        "A known MEXC/Gate/router hit is only flagged if the recipient matches the built-in known label list."
    ),
}

Path("oldcell_458b_child_wallet_batch_summary.json").write_text(json.dumps(result, indent=2))

print("==============================")
print("BATCH TRACE COMPLETE")
print("==============================")
print(f"Events saved: {len(all_events)}")
print("Saved:")
print("- oldcell_458b_child_wallet_events.csv")
print("- oldcell_458b_child_wallet_summary.csv")
print("- oldcell_458b_child_wallet_batch_summary.json")
