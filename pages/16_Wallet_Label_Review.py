from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Wallet Label Review | CF20 Audit",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

REVIEW = Path("wallet_label_priority_review.csv")
KNOWN = Path("known_wallet_labels.csv")

st.title("🏷️ Wallet Label Review")
st.caption("Prioritised list of high-volume unclassified wallets requiring manual label verification.")

def load_csv(path):
    try:
        return pd.read_csv(path) if path.exists() else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

review = load_csv(REVIEW)
known = load_csv(KNOWN)

st.info(
    "Label the largest wallets first. Use Etherscan labels, contract names, methods, token transfer behavior, "
    "and whether the address is CEX, DEX router, LP/pool, MEV, bridge, distributor, custody, or user wallet."
)

if review.empty:
    st.warning("wallet_label_priority_review.csv not found. Run `python3 rank_unclassified_wallets.py` first.")
else:
    for col in ["incoming_cell_all_dataset", "outgoing_cell_all_dataset", "net_cell_all_dataset", "total_volume_cell"]:
        if col in review.columns:
            review[col] = pd.to_numeric(review[col], errors="coerce").fillna(0)

    search = st.text_input("Search", placeholder="address, hint, notes...")
    filtered = review.copy()

    if search:
        s = search.lower()
        mask = filtered.astype(str).apply(lambda row: row.str.lower().str.contains(s, na=False).any(), axis=1)
        filtered = filtered[mask]

    if "total_volume_cell" in filtered.columns:
        filtered = filtered.sort_values("total_volume_cell", ascending=False)

    display = filtered.copy()
    for col in ["incoming_cell_all_dataset", "outgoing_cell_all_dataset", "net_cell_all_dataset", "total_volume_cell"]:
        if col in display.columns:
            display[col] = display[col].map(lambda x: f"{x:,.2f}")

    cols = [c for c in [
        "address", "first_seen_hop",
        "incoming_cell_all_dataset", "outgoing_cell_all_dataset", "net_cell_all_dataset", "total_volume_cell",
        "incoming_edges", "outgoing_edges",
        "suggested_review", "classification_hint", "manual_label", "manual_class", "notes"
    ] if c in display.columns]

    st.dataframe(display[cols].head(300), use_container_width=True, hide_index=True)

    st.download_button(
        "Download filtered review CSV",
        filtered[cols].to_csv(index=False).encode("utf-8"),
        file_name="filtered_wallet_label_priority_review.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown("## Known Wallet Labels")

if known.empty:
    st.caption("known_wallet_labels.csv not found yet.")
else:
    st.dataframe(known, use_container_width=True, hide_index=True)

st.markdown("## Add labels")

st.code(
    """
cat >> known_wallet_labels.csv <<'CSV'
address,manual_label,manual_class,notes
0xfd64fa5976687c2048f08f5df89c9a78e31df680,Bridge Lock/Unlock Contract,BRIDGE_CLUSTER,Etherscan shows Lock Token and Unlock Token methods
0xe6a2eca14d2b1b0a82dd9a407488004939fb5aad,Uniswap V3: CELL 2,LP_OR_POOL,CELL/WETH Uniswap pool
CSV

python3 trace_bridge_cluster.py --max-hops 5 --min-amount 1000 --max-edges-per-node 75
python3 rank_unclassified_wallets.py
python3 build_bridge_infrastructure_summary.py
""",
    language="bash",
)
