import json
import time
from pathlib import Path
from web3 import Web3

ETH_RPC = "https://eth.llamarpc.com"
ETH_TOKEN = "0x26c8afbbfe1ebaca03c2bb082e69d0476bffe099"

START_BLOCK = 0
STEP = 25_000

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()

w3 = Web3(Web3.HTTPProvider(ETH_RPC))

progress_file = DATA_DIR / "eth_transfer_progress.json"
out_file = DATA_DIR / "eth_transfers.jsonl"

if progress_file.exists():
    progress = json.loads(progress_file.read_text())
    current = progress["last_block"] + 1
else:
    current = START_BLOCK

latest = w3.eth.block_number

print(f"Scanning ETH transfers {current} → {latest}")

while current <= latest:
    to_block = min(current + STEP - 1, latest)

    try:
        logs = w3.eth.get_logs({
            "fromBlock": current,
            "toBlock": to_block,
            "address": Web3.to_checksum_address(ETH_TOKEN),
            "topics": [TRANSFER_TOPIC],
        })

        with out_file.open("a") as f:
            for log in logs:
                topics = log["topics"]

                from_addr = "0x" + topics[1].hex()[-40:]
                to_addr = "0x" + topics[2].hex()[-40:]
                amount = int(log["data"].hex(), 16)

                row = {
                    "chain": "eth",
                    "block": log["blockNumber"],
                    "tx_hash": log["transactionHash"].hex(),
                    "from": Web3.to_checksum_address(from_addr),
                    "to": Web3.to_checksum_address(to_addr),
                    "amount": str(amount),
                }

                f.write(json.dumps(row) + "\n")

        progress_file.write_text(json.dumps({
            "last_block": to_block,
            "latest_seen": latest,
        }))

        print(f"Scanned {current} → {to_block}, logs={len(logs)}")
        current = to_block + 1
        time.sleep(0.25)

    except Exception as e:
        print(f"Error {current} → {to_block}: {e}")
        time.sleep(5)
