import json
from pathlib import Path

import pandas as pd
import streamlit as st

SUMMARY = Path("bridge_infrastructure_summary.json")
TERMINALS = Path("bridge_cluster_terminal_endpoints.csv")
MARKET_SUMMARY = Path("bridge_market_route_summary.json")


def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except Exception:
        return default


def load_csv(path):
    try:
        return pd.read_csv(path) if path.exists() else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fmt(n):
    try:
        return f"{float(n):,.2f}"
    except Exception:
        return "—"


def render_bridge_showcase():
    data = load_json(SUMMARY)
    metrics = data.get("cluster_metrics", {})
    terminals = load_csv(TERMINALS)

    st.markdown("## 🧭 Bridge Infrastructure & Market Route Evidence")

    st.info(
        "New finding: bridge lock/unlock infrastructure has now been identified. "
        "The audit also identifies downstream CEX, DEX/router, and MEV route exposure. "
        "Route-exposure figures are not exact final sale amounts."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reachable wallets", f"{int(metrics.get('reachable_wallets') or 0):,}")
    c2.metric("Transfer edges", f"{int(metrics.get('discovered_edges') or 0):,}")
    c3.metric("Terminal endpoints", f"{int(metrics.get('terminal_endpoint_count') or 0):,}")
    c4.metric("Unclassified wallets", f"{int(metrics.get('unclassified_wallet_count') or 0):,}")

    st.markdown(
        """
<div style="border:1px solid rgba(148,163,184,.2);background:linear-gradient(145deg,rgba(15,23,42,.94),rgba(8,20,36,.88));border-radius:16px;padding:18px;margin-top:10px;">
  <div style="font-weight:950;color:#f8fafc;font-size:1.1rem;margin-bottom:10px;">Updated bridge model</div>
  <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;color:#cbd5e1;">
    <div style="padding:10px 12px;border-radius:12px;background:rgba(59,130,246,.13);border:1px solid rgba(59,130,246,.25);"><b>0xfd64...</b><br>Lock / Unlock</div>
    <div style="font-size:1.6rem;color:#38bdf8;">→</div>
    <div style="padding:10px 12px;border-radius:12px;background:rgba(59,130,246,.13);border:1px solid rgba(59,130,246,.25);"><b>0x4A831...</b><br>Bridge Token Intake</div>
    <div style="font-size:1.6rem;color:#38bdf8;">→</div>
    <div style="padding:10px 12px;border-radius:12px;background:rgba(59,130,246,.13);border:1px solid rgba(59,130,246,.25);"><b>0x35ce...</b><br>Aggregator</div>
    <div style="font-size:1.6rem;color:#38bdf8;">→</div>
    <div style="padding:10px 12px;border-radius:12px;background:rgba(245,158,11,.13);border:1px solid rgba(245,158,11,.25);"><b>0x50ebb / 0x65def / 0xd3ec</b><br>Distribution Cluster</div>
    <div style="font-size:1.6rem;color:#f59e0b;">→</div>
    <div style="padding:10px 12px;border-radius:12px;background:rgba(239,68,68,.13);border:1px solid rgba(239,68,68,.25);"><b>Gate.io / MEXC / Uniswap / 1inch / MEV</b><br>Market Endpoints</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### Key bridge contracts / wallets")
    contracts = pd.DataFrame(data.get("bridge_contracts", []))
    if not contracts.empty:
        st.dataframe(contracts, use_container_width=True, hide_index=True)

    st.markdown("### Terminal market endpoints")
    if terminals.empty:
        st.caption("bridge_cluster_terminal_endpoints.csv not found.")
    else:
        show = terminals.copy()
        if "terminal_inflow_possible_cell" in show.columns:
            show["terminal_inflow_possible_cell"] = pd.to_numeric(show["terminal_inflow_possible_cell"], errors="coerce").fillna(0)
            show = show.sort_values("terminal_inflow_possible_cell", ascending=False)
            show["terminal_inflow_possible_cell"] = show["terminal_inflow_possible_cell"].map(lambda x: f"{x:,.2f}")
        cols = [c for c in ["label", "class", "address", "terminal_inflow_possible_cell", "paths"] if c in show.columns]
        st.dataframe(show[cols].head(20), use_container_width=True, hide_index=True)

    st.caption(
        "Audit caveat: route-exposure totals should not be treated as exact final sale amounts. "
        "They show that the bridge-linked graph reaches market infrastructure."
    )
