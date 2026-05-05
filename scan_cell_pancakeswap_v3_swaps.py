import csv
import json
import os
import time
from pathlib import Path

import requests
from web3 import Web3

# ==============================
# CONFIG
# ==============================

BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")

# BSC/BEP20 CELL token and known PancakeSwap v3 WBNB/CELL pool
CELL_TOKEN = Web3.to_checksum_address("0xd98438889Ae7364c7E2A3540547Fad042FB24642")
POOL_ADDRESS = Web3.to_checksum_address(os.getenv("CELL_V3_POOL", "0xA2C1e0237bF4B58bC9808A579715dF57522F41b2"))

START_BLOCK = int(os.getenv("START_BLOCK", "30000000"))
END_BLOCK = os.getenv("END_BLOCK", "")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2000"))
SLEEP_SECONDS = float(os.getenv("SLEEP_SECONDS", "0.15"))

OUT_CSV = Path("cell_dex_swaps.csv")
OUT_JSON = Path("cell_dex_swaps_summary.json")

# PancakeSwap/Uniswap v3 pool Swap event:
# Swap(address indexed sender,address indexed recipient,int256 amount0,int256 amount1,uint160 sqrtPriceX96,uint128 liquidity,int24 tick)
SWAP_TOPIC = Web3.keccak(
    text="Swap(address,address,int256,int256,uint160,uint128,int24)"
).hex()

POOL_ABI = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

ERC20_ABI = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def rpc_latest_block():
    payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
    r = requests.post(BSC_RPC, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return int(data["result"], 16)


def topic_to_addr(topic):
    return "0x" + str(topic)[-40:].lower()


def twos_complement_int256(hex_word):
    value = int(hex_word, 16)
    if value >= 2**255:
        value -= 2**256
    return value


def decode_swap_log(log, token0, token1, token0_decimals, token1_decimals, token0_symbol, token1_symbol):
    topics = log.get("topics", [])
    data = log.get("data", "0x")[2:]

    if len(topics) < 3 or len(data) < 64 * 5:
        return None

    sender = topic_to_addr(topics[1])
    recipient = topic_to_addr(topics[2])

    words = [data[i:i + 64] for i in range(0, len(data), 64)]

    amount0_raw = twos_complement_int256(words[0])
    amount1_raw = twos_complement_int256(words[1])
    sqrt_price_x96 = int(words[2], 16)
    liquidity = int(words[3], 16)
    tick = twos_complement_int256(words[4])

    amount0 = amount0_raw / (10 ** token0_decimals)
    amount1 = amount1_raw / (10 ** token1_decimals)

    if token0.lower() == CELL_TOKEN.lower():
        cell_amount = amount0
        other_amount = amount1
        other_symbol = token1_symbol
        other_token = token1
    elif token1.lower() == CELL_TOKEN.lower():
        cell_amount = amount1
        other_amount = amount0
        other_symbol = token0_symbol
        other_token = token0
    else:
        cell_amount = 0
        other_amount = 0
        other_symbol = "UNKNOWN"
        other_token = ""

    # In v3 pool Swap logs, positive token amount means token moved into the pool.
    # If CELL is positive, CELL entered the pool: user sold CELL.
    # If CELL is negative, CELL left the pool: user bought CELL.
    if cell_amount > 0:
        cell_direction = "CELL sold into pool"
    elif cell_amount < 0:
        cell_direction = "CELL bought from pool"
    else:
        cell_direction = "No CELL delta"

    return {
        "chain": "bsc",
        "pool": POOL_ADDRESS.lower(),
        "block": int(log.get("blockNumber", 0), 16) if isinstance(log.get("blockNumber"), str) else int(log.get("blockNumber", 0)),
        "tx_hash": log.get("transactionHash", ""),
        "log_index": int(log.get("logIndex", 0), 16) if isinstance(log.get("logIndex"), str) else int(log.get("logIndex", 0)),
        "sender": sender,
        "recipient": recipient,
        "token0": token0.lower(),
        "token1": token1.lower(),
        "token0_symbol": token0_symbol,
        "token1_symbol": token1_symbol,
        "amount0": amount0,
        "amount1": amount1,
        "cell_amount_signed": cell_amount,
        "cell_amount_abs": abs(cell_amount),
        "other_token": other_token.lower(),
        "other_symbol": other_symbol,
        "other_amount_signed": other_amount,
        "other_amount_abs": abs(other_amount),
        "cell_direction": cell_direction,
        "sqrt_price_x96": sqrt_price_x96,
        "liquidity": liquidity,
        "tick": tick,
    }


def get_logs(w3, from_block, to_block):
    return w3.eth.get_logs(
        {
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": POOL_ADDRESS,
            "topics": [SWAP_TOPIC],
        }
    )


def main():
    w3 = Web3(Web3.HTTPProvider(BSC_RPC))

    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to BSC_RPC: {BSC_RPC}")

    pool = w3.eth.contract(address=POOL_ADDRESS, abi=POOL_ABI)

    token0 = Web3.to_checksum_address(pool.functions.token0().call())
    token1 = Web3.to_checksum_address(pool.functions.token1().call())

    t0 = w3.eth.contract(address=token0, abi=ERC20_ABI)
    t1 = w3.eth.contract(address=token1, abi=ERC20_ABI)

    try:
        token0_decimals = int(t0.functions.decimals().call())
    except Exception:
        token0_decimals = 18

    try:
        token1_decimals = int(t1.functions.decimals().call())
    except Exception:
        token1_decimals = 18

    try:
        token0_symbol = str(t0.functions.symbol().call())
    except Exception:
        token0_symbol = "TOKEN0"

    try:
        token1_symbol = str(t1.functions.symbol().call())
    except Exception:
        token1_symbol = "TOKEN1"

    end_block = int(END_BLOCK) if END_BLOCK else rpc_latest_block()

    print("\n==============================")
    print("CELL PANCAKESWAP V3 DEX SWAP SCANNER")
    print("==============================\n")

    print(f"RPC:           {BSC_RPC}")
    print(f"Pool:          {POOL_ADDRESS}")
    print(f"Token0:        {token0_symbol} {token0}")
    print(f"Token1:        {token1_symbol} {token1}")
    print(f"CELL token:    {CELL_TOKEN}")
    print(f"Start block:   {START_BLOCK:,}")
    print(f"End block:     {end_block:,}")
    print(f"Chunk size:    {CHUNK_SIZE:,}")

    rows = []
    current = START_BLOCK

    while current <= end_block:
        to_block = min(current + CHUNK_SIZE - 1, end_block)

        try:
            logs = get_logs(w3, current, to_block)

            for log in logs:
                parsed = decode_swap_log(
                    {
                        "topics": [Web3.to_hex(t) for t in log["topics"]],
                        "data": Web3.to_hex(log["data"]),
                        "blockNumber": log["blockNumber"],
                        "transactionHash": Web3.to_hex(log["transactionHash"]),
                        "logIndex": log["logIndex"],
                    },
                    token0,
                    token1,
                    token0_decimals,
                    token1_decimals,
                    token0_symbol,
                    token1_symbol,
                )

                if parsed:
                    rows.append(parsed)

            print(
                f"Scanned {current:,}->{to_block:,} | "
                f"swaps={len(logs):,} | total={len(rows):,}"
            )

        except Exception as e:
            print(f"Error {current:,}->{to_block:,}: {e}")
            print("Retry this range with smaller CHUNK_SIZE if needed.")

        current = to_block + 1
        time.sleep(SLEEP_SECONDS)

    rows.sort(key=lambda r: (r["block"], r["log_index"]))

    fieldnames = [
        "chain",
        "pool",
        "block",
        "tx_hash",
        "log_index",
        "sender",
        "recipient",
        "token0_symbol",
        "token1_symbol",
        "token0",
        "token1",
        "amount0",
        "amount1",
        "cell_amount_signed",
        "cell_amount_abs",
        "other_symbol",
        "other_token",
        "other_amount_signed",
        "other_amount_abs",
        "cell_direction",
        "sqrt_price_x96",
        "liquidity",
        "tick",
    ]

    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total_sold = sum(r["cell_amount_abs"] for r in rows if r["cell_direction"] == "CELL sold into pool")
    total_bought = sum(r["cell_amount_abs"] for r in rows if r["cell_direction"] == "CELL bought from pool")

    unique_senders = len(set(r["sender"] for r in rows))
    unique_recipients = len(set(r["recipient"] for r in rows))

    summary = {
        "pool": POOL_ADDRESS.lower(),
        "token0": token0.lower(),
        "token1": token1.lower(),
        "token0_symbol": token0_symbol,
        "token1_symbol": token1_symbol,
        "cell_token": CELL_TOKEN.lower(),
        "start_block": START_BLOCK,
        "end_block": end_block,
        "swap_count": len(rows),
        "unique_senders": unique_senders,
        "unique_recipients": unique_recipients,
        "cell_sold_into_pool": total_sold,
        "cell_bought_from_pool": total_bought,
        "output_csv": str(OUT_CSV),
        "note": "Positive CELL delta means CELL entered the pool, interpreted as CELL sold into the pool. Negative CELL delta means CELL left the pool, interpreted as CELL bought from the pool.",
    }

    OUT_JSON.write_text(json.dumps(summary, indent=2))

    print("\n==============================")
    print("DONE")
    print("==============================\n")

    print(f"Swaps found:            {len(rows):,}")
    print(f"Unique senders:         {unique_senders:,}")
    print(f"Unique recipients:      {unique_recipients:,}")
    print(f"CELL sold into pool:    {total_sold:,.2f}")
    print(f"CELL bought from pool:  {total_bought:,.2f}")
    print(f"Saved:                  {OUT_CSV}")
    print(f"Summary:                {OUT_JSON}")


if __name__ == "__main__":
    main()
