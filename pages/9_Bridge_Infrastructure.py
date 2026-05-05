import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Bridge Infrastructure | CF20 Audit",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

SUMMARY = Path("bridge_infrastructure_summary.json")
TERMINALS = Path("bridge_cluster_terminal_endpoints.csv")
UNCLASSIFIED = Path("bridge_cluster_unclassified_wallets.csv")
PATHS = Path("bridge_cluster_paths.csv")
KNOWN_LABELS = Path("known_wallet_labels.csv")

st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 22% 12%, rgba(59,130,246,.16), transparent 25%),
        radial-gradient(circle at 80% 18%, rgba(245,158,11,.12), transparent 20%),
        #050d18;
}
.block-container { max-width: 1600px; padding-top: 1rem; }
#MainMenu, header, footer { visibility: hidden; }
.panel {
    border:1px solid rgba(148,163,184,.18);
    background:linear-gradient(145deg, rgba(15,23,42,.94), rgba(8,20,36,.88));
    border-radius:18px;
    padding:18px;
    box-shadow:0 18px 40px rgba(0,0,0,.22);
}
.card {
    border:1px solid rgba(148,163,184,.18);
    background:rgba(8,18,34,.78);
    border-radius:18px;
    padding:16px;
    min-height:165px;
}
.card-title { color:#f8fafc;font-size:1rem;font-weight:950;margin-bottom:8px; }
.card-copy { color:#cbd5e1;font-size:.92rem;line-height:1.55; }
.chip {
    display:inline-block;
    border-radius:999px;
    padding:4px 9px;
    font-size:.76rem;
    font-weight:850;
    margin-right:6px;
    margin-bottom:6px;
}
.blue { color:#93c5fd; border:1px solid rgba(59,130,246,.35); background:rgba(59,130,246,.12); }
.red { color:#fca5a5; border:1px solid rgba(239,68,68,.35); background:rgba(239,68,68,.12); }
.orange { color:#fcd34d; border:1px solid rgba(245,158,11,.35); background:rgba(245,158,11,.12); }
.green { color:#86efac; border:1px solid rgba(34,197,94,.35); background:rgba(34,197,94,.12); }
.purple { color:#d8b4fe; border:1px solid rgba(168,85,247,.35); background:rgba(168,85,247,.12); }
.flow {
    display:flex;
    gap:12px;
    align-items:stretch;
    flex-wrap:wrap;
    color:#cbd5e1;
}
.node {
    padding:13px 14px;
    border-radius:14px;
    background:rgba(15,23,42,.88);
    border:1px solid rgba(148,163,184,.22);
    min-width:165px;
    flex:1;
}
.node b { color:#f8fafc; }
.node span { color:#94a3b8;font-size:.82rem;line-height:1.45; }
.arrow { color:#38bdf8;font-size:1.8rem;font-weight:950;display:flex;align-items:center; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
code { color:#93c5fd;background:rgba(15,23,42,.88);padding:2px 5px;border-radius:6px; }
</style>
""",
    unsafe_allow_html=True,
)


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


data = load_json(SUMMARY)
metrics = data.get("cluster_metrics", {})

st.title("🌉 Bridge Infrastructure Evidence")
st.caption("Bridge lock/unlock contract, intake/router, aggregator, downstream distribution cluster, and terminal market endpoints.")

if not SUMMARY.exists():
    st.warning("bridge_infrastructure_summary.json not found. Run `python3 build_bridge_infrastructure_summary.py` first.")

st.markdown(
    """
<div class="panel">
  <span class="chip green">New finding</span>
  <span class="chip blue">Bridge infrastructure identified</span>
  <span class="chip red">Market-route exposure identified</span>
  <div style="font-weight:950;color:#f8fafc;font-size:1.2rem;margin:8px 0;">Core conclusion</div>
  <div style="color:#cbd5e1;line-height:1.65;">
    The audit has identified a bridge lock/unlock endpoint: <b>0xfd64fa5976687c2048f08f5df89c9a78e31df680</b>.
    Its transaction history shows <b>Lock Token</b> and <b>Unlock Token</b> methods, including routes to
    <b>0x4A831...</b> and <b>0x35ce...</b>.
    The wider graph routes onward into CEX, DEX/router, and MEV infrastructure.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Reachable wallets", f"{int(metrics.get('reachable_wallets') or 0):,}")
c2.metric("Discovered edges", f"{int(metrics.get('discovered_edges') or 0):,}")
c3.metric("Terminal endpoints", f"{int(metrics.get('terminal_endpoint_count') or 0):,}")
c4.metric("Unclassified wallets", f"{int(metrics.get('unclassified_wallet_count') or 0):,}")

st.markdown("## Infographic Flow")

st.markdown(
    """
<div class="panel">
  <div class="flow">
    <div class="node"><b>0xfd64...</b><br><span>Bridge Lock / Unlock<br>Lock Token + Unlock Token</span></div>
    <div class="arrow">→</div>
    <div class="node"><b>0x4A831...</b><br><span>Bridge Token Intake<br>User-facing calls</span></div>
    <div class="arrow">→</div>
    <div class="node"><b>0x35ce...</b><br><span>Bridge Aggregator<br>Routes onward</span></div>
    <div class="arrow">→</div>
    <div class="node"><b>0x50ebb / 0x65def / 0xd3ec</b><br><span>Distribution Cluster<br>Multi-hop movement</span></div>
    <div class="arrow">→</div>
    <div class="node"><b>0xda8a / 0x9c4...</b><br><span>Consolidation / Router Hub<br>CEX + DEX routes</span></div>
    <div class="arrow">→</div>
    <div class="node"><b>Gate.io / MEXC / Uniswap / 1inch</b><br><span>Market Infrastructure<br>CEX, DEX, MEV</span></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("## Evidence Cards")

a, b, c, d = st.columns(4)

cards = [
    ("1. Lock/Unlock contract", "0xfd64... shows Lock Token and Unlock Token methods and routes to known bridge infrastructure.", "green", "Bridge"),
    ("2. Intake/router", "0x4A831... receives Bridge Token calls and routes through the bridge cluster.", "blue", "Intake"),
    ("3. Distribution cluster", "0x35ce..., 0x50ebb..., 0x65def..., 0xd3ec..., and 0xda8a... form the downstream routing graph.", "orange", "Cluster"),
    ("4. Market endpoints", "Traversal reaches Gate.io, MEXC, MetaMask Swaps, Uniswap, 1inch, ParaSwap, CoW, and MEV infrastructure.", "red", "Market"),
]

for col, (title, copy, chip_class, chip) in zip([a, b, c, d], cards):
    with col:
        st.markdown(
            f"""
<div class="card">
  <div class="card-title">{title}</div>
  <div class="card-copy">{copy}</div>
  <br>
  <span class="chip {chip_class}">{chip}</span>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown("## Bridge Contracts / Cluster Wallets")

contracts = pd.DataFrame(data.get("bridge_contracts", []))
cluster = pd.DataFrame(data.get("bridge_cluster", []))

left, right = st.columns([1.2, 1])

with left:
    st.markdown("### Core contracts")
    if contracts.empty:
        st.info("No bridge contract summary found.")
    else:
        st.dataframe(contracts, use_container_width=True, hide_index=True)

with right:
    st.markdown("### Downstream cluster")
    if cluster.empty:
        st.info("No bridge cluster summary found.")
    else:
        st.dataframe(cluster, use_container_width=True, hide_index=True)

st.markdown("## Terminal Market Endpoints")

terminals = load_csv(TERMINALS)

if terminals.empty:
    st.info("bridge_cluster_terminal_endpoints.csv not found.")
else:
    show = terminals.copy()
    if "terminal_inflow_possible_cell" in show.columns:
        show["terminal_inflow_possible_cell"] = pd.to_numeric(show["terminal_inflow_possible_cell"], errors="coerce").fillna(0)
        show = show.sort_values("terminal_inflow_possible_cell", ascending=False)
        show["terminal_inflow_possible_cell"] = show["terminal_inflow_possible_cell"].map(lambda x: f"{x:,.2f}")

    cols = [c for c in ["label", "class", "address", "terminal_inflow_possible_cell", "paths", "direct_edge_count"] if c in show.columns]
    st.dataframe(show[cols], use_container_width=True, hide_index=True)

st.markdown("## High-Volume Unclassified Wallets")

unclassified = load_csv(UNCLASSIFIED)

if unclassified.empty:
    st.info("bridge_cluster_unclassified_wallets.csv not found.")
else:
    review = unclassified.copy()
    for col in ["incoming_cell_all_dataset", "outgoing_cell_all_dataset", "net_cell_all_dataset"]:
        if col in review.columns:
            review[col] = pd.to_numeric(review[col], errors="coerce").fillna(0)

    review = review.sort_values("outgoing_cell_all_dataset", ascending=False).head(50)
    display = review.copy()

    for col in ["incoming_cell_all_dataset", "outgoing_cell_all_dataset", "net_cell_all_dataset"]:
        if col in display.columns:
            display[col] = display[col].map(lambda x: f"{x:,.2f}")

    cols = [c for c in ["address", "first_seen_hop", "incoming_cell_all_dataset", "outgoing_cell_all_dataset", "net_cell_all_dataset", "incoming_edges", "outgoing_edges", "suggested_review"] if c in display.columns]
    st.dataframe(display[cols], use_container_width=True, hide_index=True)

st.markdown("## Audit Caveat")

st.warning(
    data.get(
        "important_note",
        "Route exposure totals are not exact final sale amounts because paths can overlap, loop, or terminate inside centralized exchanges where internal trades are off-chain.",
    )
)

st.markdown("## Downloads")

download_cols = st.columns(4)

files = [
    ("Bridge infrastructure summary", SUMMARY, "application/json"),
    ("Terminal endpoints", TERMINALS, "text/csv"),
    ("Cluster paths", PATHS, "text/csv"),
    ("Known wallet labels", KNOWN_LABELS, "text/csv"),
]

for col, (label, path, mime) in zip(download_cols, files):
    with col:
        if path.exists():
            st.download_button(label, path.read_bytes(), file_name=path.name, mime=mime, use_container_width=True)
        else:
            st.caption(f"Missing: {path.name}")
