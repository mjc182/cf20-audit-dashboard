import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Verified Wallets",
    page_icon="💼",
    layout="wide",
)

BALANCES_FILE = Path("verified_wallet_balances.json")
REGISTRY_FILE = Path("verified_wallets.json")
SUMMARY_FILE = Path("verified_wallet_summary.json")


def load_json(path, default):
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def flatten_registry(registry):
    rows = []

    for chain, groups in registry.items():
        for group, wallets in groups.items():
            for label, address in wallets.items():
                rows.append(
                    {
                        "chain": chain,
                        "group": group,
                        "label": label,
                        "address": str(address).lower(),
                    }
                )

    return pd.DataFrame(rows)


def load_balances():
    rows = load_json(BALANCES_FILE, [])

    if not rows:
        return pd.DataFrame(
            columns=[
                "chain",
                "group",
                "label",
                "address",
                "balance_tokens",
                "supply_percent",
                "token_contract",
            ]
        )

    df = pd.DataFrame(rows)

    if "address" in df.columns:
        df["address"] = df["address"].astype(str).str.lower()

    return df


st.title("💼 Verified Wallets")
st.caption(
    "Verified ETH and BSC wallets used for bridge, exchange, LP, and trace classification."
)

registry = load_json(REGISTRY_FILE, {})
balances = load_balances()

if not registry:
    st.error(
        "verified_wallets.json is missing or empty. Upload/create it in the repo root."
    )
    st.stop()

registry_df = flatten_registry(registry)

if registry_df.empty:
    st.error("verified_wallets.json loaded but no wallets were found.")
    st.stop()

st.markdown("## Registry Coverage")

c1, c2, c3, c4 = st.columns(4)

eth_count = int((registry_df["chain"] == "eth").sum())
bsc_count = int((registry_df["chain"] == "bsc").sum())
group_count = registry_df["group"].nunique()
total_count = len(registry_df)

c1.metric("Total verified wallets", f"{total_count:,}")
c2.metric("ETH wallets", f"{eth_count:,}")
c3.metric("BSC wallets", f"{bsc_count:,}")
c4.metric("Groups", f"{group_count:,}")

st.markdown("## Verified Wallet Registry")

show_registry = registry_df.copy()
st.dataframe(
    show_registry[["chain", "group", "label", "address"]],
    use_container_width=True,
    hide_index=True,
)

st.markdown("## Balance Tracking Status")

if balances.empty:
    st.warning(
        "No verified_wallet_balances.json found, or the file is empty. "
        "The registry is visible, but balances have not been scanned yet. "
        "For ETH balances, set ETH_RPC before running track_verified_wallets.py."
    )
else:
    merged = registry_df.merge(
        balances[
            [
                "chain",
                "group",
                "label",
                "address",
                "balance_tokens",
                "supply_percent",
                "token_contract",
            ]
        ],
        on=["chain", "group", "label", "address"],
        how="left",
    )

    merged["balance_status"] = merged["balance_tokens"].apply(
        lambda x: "scanned" if pd.notna(x) else "not scanned / RPC missing"
    )

    merged["balance_tokens"] = pd.to_numeric(
        merged["balance_tokens"],
        errors="coerce",
    ).fillna(0)

    merged["supply_percent"] = pd.to_numeric(
        merged["supply_percent"],
        errors="coerce",
    ).fillna(0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Scanned wallets", f"{int((merged['balance_status'] == 'scanned').sum()):,}")
    c2.metric("Tracked CELL balance", f"{merged['balance_tokens'].sum():,.2f}")
    c3.metric("Tracked supply %", f"{merged['supply_percent'].sum():,.4f}%")

    display = merged.copy()
    display["balance_tokens"] = display["balance_tokens"].map(lambda x: f"{x:,.2f}")
    display["supply_percent"] = display["supply_percent"].map(lambda x: f"{x:,.4f}%")

    st.dataframe(
        display[
            [
                "chain",
                "group",
                "label",
                "address",
                "balance_tokens",
                "supply_percent",
                "balance_status",
                "token_contract",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("## Category Totals")

    totals = merged.groupby(["chain", "group"], as_index=False).agg(
        balance_tokens=("balance_tokens", "sum"),
        supply_percent=("supply_percent", "sum"),
        wallets=("address", "count"),
    )

    totals["balance_tokens"] = totals["balance_tokens"].map(lambda x: f"{x:,.2f}")
    totals["supply_percent"] = totals["supply_percent"].map(lambda x: f"{x:,.4f}%")

    st.dataframe(
        totals,
        use_container_width=True,
        hide_index=True,
    )

st.markdown("## Raw Registry")

with st.expander("View verified_wallets.json"):
    st.json(registry)
