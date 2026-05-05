import json
import os
from pathlib import Path
from web3 import Web3

SCALE = 10**18

ETH_TOKEN = "0x26c8afbbfe1ebaca03c2bb082e69d0476bffe099"
BSC_TOKEN = "0xd98438889Ae7364c7E2A3540547Fad042FB24642"

ETH_RPC = os.getenv("ETH_RPC", "")
BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")

REGISTRY_FILE = Path("verified_wallets.json")
OUT_FILE = Path("verified_wallet_balances.json")

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
]


def get_contract(rpc_url, token_address):
    if not rpc_url:
        return None, None

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(token_address),
        abi=ERC20_ABI,
    )
    return w3, contract


def main():
    if not REGISTRY_FILE.exists():
        raise FileNotFoundError("Missing verified_wallets.json")

    registry = json.loads(REGISTRY_FILE.read_text())

    chains = {
        "eth": {
            "rpc": ETH_RPC,
            "token": ETH_TOKEN,
        },
        "bsc": {
            "rpc": BSC_RPC,
            "token": BSC_TOKEN,
        },
    }

    results = []

    for chain, groups in registry.items():
        if chain not in chains:
            continue

        rpc = chains[chain]["rpc"]
        token_address = chains[chain]["token"]

        w3, token = get_contract(rpc, token_address)

        if token is None:
            print(f"Skipping {chain.upper()} — RPC missing")
            continue

        total_supply = token.functions.totalSupply().call()

        for group, wallets in groups.items():
            for label, address in wallets.items():
                try:
                    balance_raw = token.functions.balanceOf(
                        Web3.to_checksum_address(address)
                    ).call()

                    balance_tokens = balance_raw / SCALE
                    supply_percent = (balance_raw / total_supply) * 100 if total_supply else 0

                    row = {
                        "chain": chain,
                        "group": group,
                        "label": label,
                        "address": address,
                        "balance_raw": str(balance_raw),
                        "balance_tokens": balance_tokens,
                        "supply_percent": supply_percent,
                    }

                    results.append(row)

                    print(
                        f"{chain.upper()} | {group} | {label} | "
                        f"{balance_tokens:,.2f} CELL | {supply_percent:.4f}%"
                    )

                except Exception as e:
                    print(f"Error checking {chain} {label} {address}: {e}")

    OUT_FILE.write_text(json.dumps(results, indent=2))
    print(f"\nSaved: {OUT_FILE}")


if __name__ == "__main__":
    main()