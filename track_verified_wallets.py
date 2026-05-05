import json
import os
from pathlib import Path

from web3 import Web3

SCALE = 10**18

# Correct token contracts
ETH_CELL_TOKEN = "0x26c8afbbfe1ebaca03c2bb082e69d0476bffe099"
BSC_CELL_TOKEN = "0xd98438889Ae7364c7E2A3540547Fad042FB24642"

ETH_RPC = os.getenv("ETH_RPC", "")
BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")

OUT_WALLETS = Path("verified_wallets.json")
OUT_BALANCES = Path("verified_wallet_balances.json")
OUT_SUMMARY = Path("verified_wallet_summary.json")

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "supply", "type": "uint256"}],
        "type": "function",
    },
]

VERIFIED_WALLETS = {
    "eth": {
        "bridge": {
            "Bridge Intake": "0x4a831a8ebb160ad025d34a788c99e9320b9ab531",
            "Aggregator L1": "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60",
            "Aggregator L2": "0x50ebb0827aa80ba1a2a30b38581629996262d481",
            "Secondary Distributor": "0x52105eee8e836ff9e60cb02c0a665cbe2fc3a30d",
            "Router / Exchange-like": "0x9c4cc862f51b1ba90485de3502aa058ca4331f32",
        },
        "bridge_out_destination": {
            # From Zerochain DATUM_TX: BRIDGE OUT BEP20 destination.
            # This is a BSC-format address, but included here as a known trace target.
            "BEP20 Bridge-Out Destination 0x1fa": "0x1fa6348d9b13d316c62d54f62bea4e1a7207d9d6",
        },
    },
    "bsc": {
        "exchange": {
            "MEXC 13": "0x4982085C9e2F89F2eCb8131Eca71aFAD896e89CB",
            "Gate.io 1": "0x0D0707963952f2fBA59dD06f2b425ace40b492Fe",
            "MEXC 5": "0x2e8F79aD740de90dC5F5A9F0D8D9661a60725e64",
            "BitMart 7": "0xeACB50a28630a4C44a884158eE85cBc10d2B3F10",
        },
        "liquidity_pool": {
            "PancakeSwap v3 WBNB/CELL Pool": "0xA2C1e0237bF4B58bC9808A579715dF57522F41b2",
        },
        "large_holder": {
            "Top Non-Exchange Holder": "0xe0CA82008F52Dd94a4314C4869A0294e8c136F1d",
            "Large Holder 0xEb279": "0xEb27941e000000000000000000000000f01347Ae0",
        },
        "bridge_trace": {
            "BEP20 Bridge-Out Destination 0x1fa": "0x1fa6348d9b13d316c62d54f62bea4e1a7207d9d6",
        },
    },
}


def valid_address(addr: str) -> bool:
    try:
        return Web3.is_address(addr)
    except Exception:
        return False


def checksum(addr: str) -> str:
    return Web3.to_checksum_address(addr)


def get_w3(chain: str):
    if chain == "eth":
        if not ETH_RPC:
            return None
        return Web3(Web3.HTTPProvider(ETH_RPC))

    if chain == "bsc":
        if not BSC_RPC:
            return None
        return Web3(Web3.HTTPProvider(BSC_RPC))

    return None


def get_token(chain: str):
    return ETH_CELL_TOKEN if chain == "eth" else BSC_CELL_TOKEN


def get_balance(w3, token_contract, wallet):
    try:
        return int(token_contract.functions.balanceOf(checksum(wallet)).call())
    except Exception as e:
        print(f"Error checking {wallet}: {e}")
        return 0


def get_total_supply(w3, token_contract):
    try:
        return int(token_contract.functions.totalSupply().call())
    except Exception:
        return 0


def main():
    print("\n==============================")
    print("VERIFIED WALLET BALANCE TRACKER")
    print("==============================\n")

    OUT_WALLETS.write_text(json.dumps(VERIFIED_WALLETS, indent=2))

    balance_rows = []
    summary_rows = []

    for chain, groups in VERIFIED_WALLETS.items():
        w3 = get_w3(chain)

        if w3 is None:
            print(f"{chain.upper()}: RPC missing, skipping balances")
            continue

        token_address = get_token(chain)

        if not valid_address(token_address):
            print(f"{chain.upper()}: invalid token contract {token_address}")
            continue

        token = w3.eth.contract(
            address=checksum(token_address),
            abi=ERC20_ABI,
        )

        total_supply_raw = get_total_supply(w3, token)
        total_supply_tokens = total_supply_raw / SCALE if total_supply_raw else 0

        print(f"{chain.upper()} token: {token_address}")
        print(f"{chain.upper()} total supply: {total_supply_tokens:,.2f}")

        chain_total = 0

        for group, wallets in groups.items():
            group_total = 0

            for label, address in wallets.items():
                if not valid_address(address):
                    print(f"Skipping invalid address: {label} = {address}")
                    continue

                raw = get_balance(w3, token, address)
                tokens = raw / SCALE
                supply_percent = (
                    tokens / total_supply_tokens * 100
                    if total_supply_tokens
                    else 0
                )

                group_total += tokens
                chain_total += tokens

                row = {
                    "chain": chain,
                    "group": group,
                    "label": label,
                    "address": address.lower(),
                    "balance_raw": str(raw),
                    "balance_tokens": tokens,
                    "supply_percent": supply_percent,
                    "token_contract": token_address.lower(),
                }

                balance_rows.append(row)

                print(
                    f"{chain.upper()} | {group} | {label} | "
                    f"{tokens:,.2f} CELL | {supply_percent:.4f}%"
                )

            summary_rows.append(
                {
                    "chain": chain,
                    "group": group,
                    "balance_tokens": group_total,
                    "supply_percent": (
                        group_total / total_supply_tokens * 100
                        if total_supply_tokens
                        else 0
                    ),
                }
            )

        summary_rows.append(
            {
                "chain": chain,
                "group": "ALL_TRACKED",
                "balance_tokens": chain_total,
                "supply_percent": (
                    chain_total / total_supply_tokens * 100
                    if total_supply_tokens
                    else 0
                ),
            }
        )

    OUT_BALANCES.write_text(json.dumps(balance_rows, indent=2))
    OUT_SUMMARY.write_text(json.dumps(summary_rows, indent=2))

    print("\nSaved:")
    print(f"- {OUT_WALLETS}")
    print(f"- {OUT_BALANCES}")
    print(f"- {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
