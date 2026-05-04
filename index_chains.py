import json
import time
from pathlib import Path
from web3 import Web3

ETH_RPC = "https://eth.llamarpc.com"
BSC_RPC = "https://bsc-dataseed.binance.org/"

ETH_TOKEN = "0x26c8afbbfe1ebaca03c2bb082e69d0476bffe099"
BSC_TOKEN = "0xf3e1449ddb6b218da2c9463d4594ceccc8934346"

BURN = "0x000000000000000000000000000000000000dead"
TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def topic_address(addr):
    return Web3.to_hex(Web3.to_bytes(hexstr=addr).rjust(32, b"\x00"))


def scan_chain(name, rpc, token, start_block, step=25_000):
    w3 = Web3(Web3.HTTPProvider(rpc))
    latest = w3.eth.block_number

    progress_file = DATA_DIR / f"{name}_progress.json"
    events_file = DATA_DIR / f"{name}_burns.jsonl"

    if progress_file.exists():
        progress = json.loads(progress_file.read_text())
        current = progress["last_block"] + 1
    else:
        current = start_block

    print(f"{name}: scanning {current} → {latest}")

    while current <= latest:
        to_block = min(current + step - 1, latest)

        try:
            logs = w3.eth.get_logs({
                "fromBlock": current,
                "toBlock": to_block,
                "address": Web3.to_checksum_address(token),
                "topics": [
                    TRANSFER_TOPIC,
                    None,
                    topic_address(BURN),
                ],
            })

            with events_file.open("a") as f:
                for log in logs:
                    value = int(log["data"].hex(), 16)

                    row = {
                        "chain": name,
                        "block": log["blockNumber"],
                        "tx_hash": log["transactionHash"].hex(),
                        "amount": str(value),
                    }

                    f.write(json.dumps(row) + "\n")

            progress_file.write_text(json.dumps({
                "last_block": to_block,
                "latest_seen": latest,
            }))

            print(f"{name}: scanned {current} → {to_block}, logs={len(logs)}")
            current = to_block + 1
            time.sleep(0.25)

        except Exception as e:
            print(f"{name}: error at {current} → {to_block}: {e}")
            time.sleep(5)


if __name__ == "__main__":
    scan_chain("eth", ETH_RPC, ETH_TOKEN, start_block=0)
    scan_chain("bsc", BSC_RPC, BSC_TOKEN, start_block=0)
