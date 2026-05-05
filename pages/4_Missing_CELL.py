import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Missing CELL", page_icon="⚠️", layout="wide")

CELL_PER_MCELL = 1000

WALLETS_DEDUPED = Path("missing_cell_wallets_deduped.csv")
EVENTS_DEDUPED = Path("missing_cell_events_deduped.csv")
WALLETS = Path("missing_cell_wallets.csv")
EVENTS = Path("missing_cell_events.csv")
MASTER = Path("audit_master_summary.json")

wallet_file = WALLETS_DEDUPED if WALLETS_DEDUPED.exists() else WALLETS
event_file = EVENTS_DEDUPED if EVENTS_DEDUPED.exists() else EVENTS

st.title("⚠️ Missing CELL / mCELL")
st.caption("CELL-only unmatched emissions, deduplicated where audit_master_summary has been built.")

if not wallet_file.exists() or not event_file.exists():
    st.info("Missing CELL outputs not found. Run `filter_missing_cell_only.py`, then `build_audit_master_summary.py`.")
    st.stop()

wallets = pd.read_csv(wallet_file)
events = pd.read_csv(event_file)

master = {}
if MASTER.exists():
    try:
        master = json.loads(MASTER.read_text())
    except Exception:
        master = {}

analysis = master.get("independent_chain_analysis", {})
missing_cell_total = analysis.get("deduped_unmatched_cell")

if missing_cell_total is None and "missing_cell" in wallets.columns:
    missing_cell_total = pd.to_numeric(wallets["missing_cell"], errors="coerce").sum()

missing_mcell_total = float(missing_cell_total or 0) / CELL_PER_MCELL

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Missing CELL", f"{float(missing_cell_total or 0):,.2f}")
c2.metric("mCELL Equivalent", f"{missing_mcell_total:,.2f}")
c3.metric("Duplicate events removed", f"{analysis.get('event_duplicates_removed', '—')}")
c4.metric("Recipient wallets", f"{len(wallets):,}")
c5.metric("Events", f"{len(events):,}")

st.info("Unit note: 1 mCELL = 1,000 CELL.")

st.markdown("### Top recipient wallets")
show = wallets.copy()

if "missing_cell" in show.columns:
    show["missing_cell"] = pd.to_numeric(show["missing_cell"], errors="coerce")
    show["missing_mcell_equivalent"] = show["missing_cell"] / CELL_PER_MCELL

if "share_of_missing" in show.columns:
    show["share_of_missing"] = pd.to_numeric(show["share_of_missing"], errors="coerce")

st.dataframe(show.head(100), use_container_width=True, hide_index=True)

if {"mint_to", "missing_cell"}.issubset(wallets.columns):
    chart_df = wallets.copy().head(20)
    chart_df["missing_cell"] = pd.to_numeric(chart_df["missing_cell"], errors="coerce")
    chart_df["missing_mcell_equivalent"] = chart_df["missing_cell"] / CELL_PER_MCELL
    chart_df["wallet_short"] = chart_df["mint_to"].astype(str).str[:10] + "..." + chart_df["mint_to"].astype(str).str[-6:]
    chart = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("missing_cell:Q", title="Missing CELL"),
        y=alt.Y("wallet_short:N", sort="-x", title=None),
        tooltip=[
            "mint_to:N",
            alt.Tooltip("missing_cell:Q", format=",.2f"),
            alt.Tooltip("missing_mcell_equivalent:Q", format=",.2f"),
        ],
    ).properties(height=520)
    st.altair_chart(chart, use_container_width=True)

st.markdown("### Largest unmatched CELL mint events")
events_show = events.copy()
if "mint_amount_tokens" in events_show.columns:
    events_show["mint_amount_tokens"] = pd.to_numeric(events_show["mint_amount_tokens"], errors="coerce")
    if "mint_amount_mcell_equivalent" not in events_show.columns:
        events_show["mint_amount_mcell_equivalent"] = events_show["mint_amount_tokens"] / CELL_PER_MCELL
    events_show = events_show.sort_values("mint_amount_tokens", ascending=False)

st.dataframe(events_show.head(250), use_container_width=True, hide_index=True)
