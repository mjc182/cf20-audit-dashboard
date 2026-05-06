import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="CF20 Audit | Independent Evidence Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================
# FILES
# ==============================

MASTER = Path("audit_master_summary.json")
BRIDGE_INFRA = Path("bridge_infrastructure_summary.json")
TERMINALS = Path("bridge_cluster_terminal_endpoints.csv")
UNCLASSIFIED = Path("bridge_cluster_unclassified_wallets.csv")
MISSING_WALLETS_DEDUPED = Path("missing_cell_wallets_deduped.csv")
MISSING_WALLETS = Path("missing_cell_wallets.csv")

CELL_PER_MCELL = 1000

# ==============================
# STYLE
# ==============================

st.markdown(
    """
<style>
:root {
    --bg:#050d18;
    --panel:#081426;
    --panel2:#0f172a;
    --muted:#94a3b8;
    --text:#f8fafc;
    --soft:#cbd5e1;
    --blue:#38bdf8;
    --green:#22c55e;
    --red:#ef4444;
    --orange:#f59e0b;
    --purple:#a855f7;
}
html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 15% 8%, rgba(56,189,248,.15), transparent 25%),
        radial-gradient(circle at 80% 12%, rgba(168,85,247,.12), transparent 24%),
        radial-gradient(circle at 52% 0%, rgba(34,197,94,.08), transparent 22%),
        #050d18;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07101d 0%, #06111f 100%);
    border-right: 1px solid rgba(148,163,184,.18);
}
[data-testid="stSidebar"] * { color: #dbeafe; }
.block-container { padding-top: 1rem; max-width: 1650px; }
#MainMenu, header, footer { visibility: hidden; }

.sidebar-brand {
    font-size:1.05rem;
    font-weight:950;
    padding:12px 0 14px 0;
    color:#f8fafc;
}
.sidebar-section {
    color:#94a3b8;
    font-size:.72rem;
    font-weight:850;
    margin:18px 0 6px;
    text-transform:uppercase;
    letter-spacing:.08em;
}
.hero {
    border:1px solid rgba(148,163,184,.18);
    background:
        linear-gradient(145deg, rgba(15,23,42,.96), rgba(8,20,36,.88)),
        radial-gradient(circle at 12% 10%, rgba(56,189,248,.18), transparent 28%);
    border-radius:22px;
    padding:24px 26px;
    box-shadow:0 24px 60px rgba(0,0,0,.30);
}
.hero h1 {
    margin:0;
    color:#f8fafc;
    font-size:2.25rem;
    line-height:1.08;
    letter-spacing:-.055em;
}
.hero p {
    color:#cbd5e1;
    line-height:1.65;
    font-size:1rem;
    max-width:980px;
}
.panel {
    border:1px solid rgba(148,163,184,.18);
    background:linear-gradient(145deg, rgba(15,23,42,.94), rgba(8,20,36,.88));
    border-radius:18px;
    padding:18px;
    box-shadow:0 18px 40px rgba(0,0,0,.22);
}
.kpi-card {
    border:1px solid rgba(148,163,184,.18);
    background:linear-gradient(145deg, rgba(15,23,42,.96), rgba(12,28,50,.88));
    border-radius:18px;
    padding:16px;
    min-height:112px;
    box-shadow:0 18px 40px rgba(0,0,0,.28);
}
.kpi-card .label { color:#cbd5e1; font-size:.80rem; font-weight:800; margin-bottom:8px; }
.kpi-card .value { color:#f8fafc; font-size:1.55rem; font-weight:950; letter-spacing:-.045em; }
.kpi-card .sub { margin-top:6px; font-size:.76rem; color:#94a3b8; font-weight:750; line-height:1.4; }
.audit-card {
    border:1px solid rgba(148,163,184,.18);
    background:rgba(8,18,34,.72);
    border-radius:18px;
    padding:16px;
    min-height:190px;
    position:relative;
    overflow:hidden;
}
.audit-card:before {
    content:"";
    position:absolute;
    inset:-1px;
    background:linear-gradient(90deg, rgba(56,189,248,.16), transparent 45%, rgba(168,85,247,.12));
    pointer-events:none;
}
.audit-card-inner { position:relative; z-index:1; }
.audit-num {
    width:34px;height:34px;border-radius:999px;
    display:flex;align-items:center;justify-content:center;
    font-size:.9rem;font-weight:950;color:#e0f2fe;
    background:rgba(56,189,248,.14);
    border:1px solid rgba(56,189,248,.32);
    box-shadow:0 0 22px rgba(56,189,248,.18);
}
.audit-title { color:#f8fafc; font-size:1.02rem; font-weight:950; margin-top:10px; }
.audit-copy { color:#cbd5e1; font-size:.9rem; line-height:1.58; margin-top:8px; }
.chip {
    display:inline-block;
    border-radius:999px;
    padding:4px 9px;
    font-size:.74rem;
    font-weight:850;
    margin-right:6px;
    margin-bottom:6px;
}
.chip-blue { color:#93c5fd; border:1px solid rgba(59,130,246,.35); background:rgba(59,130,246,.12); }
.chip-red { color:#fca5a5; border:1px solid rgba(239,68,68,.35); background:rgba(239,68,68,.12); }
.chip-orange { color:#fcd34d; border:1px solid rgba(245,158,11,.35); background:rgba(245,158,11,.12); }
.chip-green { color:#86efac; border:1px solid rgba(34,197,94,.35); background:rgba(34,197,94,.12); }
.chip-purple { color:#d8b4fe; border:1px solid rgba(168,85,247,.35); background:rgba(168,85,247,.12); }
.flow-wrap {
    border:1px solid rgba(148,163,184,.18);
    background:
        linear-gradient(145deg, rgba(15,23,42,.95), rgba(8,20,36,.88));
    border-radius:22px;
    padding:18px;
}
.flow-grid {
    display:grid;
    grid-template-columns: repeat(6, minmax(130px, 1fr));
    gap:10px;
    align-items:stretch;
}
.flow-node {
    border:1px solid rgba(148,163,184,.20);
    border-radius:16px;
    padding:13px 12px;
    background:rgba(15,23,42,.72);
    min-height:118px;
}
.flow-node b { color:#f8fafc; font-size:.92rem; }
.flow-node span { color:#94a3b8; font-size:.78rem; line-height:1.45; }
.flow-arrow {
    display:flex;align-items:center;justify-content:center;
    color:#38bdf8;
    font-weight:950;
    font-size:1.4rem;
    text-shadow:0 0 20px rgba(56,189,248,.35);
}
@media (max-width: 1100px) {
    .flow-grid { grid-template-columns: 1fr; }
    .flow-arrow { transform: rotate(90deg); }
}
.red { color:#ef4444 !important; }
.orange { color:#f59e0b !important; }
.blue { color:#60a5fa !important; }
.green { color:#22c55e !important; }
.purple { color:#c084fc !important; }
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }
code {
    color:#93c5fd;
    background:rgba(15,23,42,.88);
    padding:2px 5px;
    border-radius:6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================
# HELPERS
# ==============================

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


def fmt_num(n):
    try:
        n = float(n)
    except Exception:
        return "—"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:,.2f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:,.2f}K"
    return f"{n:,.2f}"


def metric_card(label, value, sub="", color=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="label">{label}</div>
            <div class="value {color}">{value}</div>
            <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar():
    st.sidebar.markdown('<div class="sidebar-brand">🛡️ CF20 Independent Audit</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-section">Main</div>', unsafe_allow_html=True)
    st.sidebar.page_link("app.py", label="Home / Executive View")

    st.sidebar.markdown('<div class="sidebar-section">Evidence</div>', unsafe_allow_html=True)

    page_links = [
        ("pages/9_Bridge_Infrastructure.py", "Bridge Infrastructure"),
        ("pages/15_Market_Route_Evidence.py", "Market Route Evidence"),
        ("pages/16_Wallet_Label_Review.py", "Wallet Label Review"),
        ("pages/1_Investigation_Graph.py", "Investigation Graph"),
        ("pages/2_Verified_Wallets.py", "Verified Wallets"),
        ("pages/3_Mint_Cross_Check.py", "Mint Cross-Check"),
        ("pages/4_Missing_CELL.py", "Missing CELL"),
        ("pages/5_Bridge_Out_Trace.py", "Bridge-Out Trace"),
        ("pages/6_Evidence_Downloads.py", "Evidence Downloads"),
        ("pages/7_Assumptions_Limitations.py", "Assumptions & Limitations"),
        ("pages/8_Evidence_Hashes.py", "Evidence Hashes"),
    ]

    for page, label in page_links:
        if Path(page).exists():
            st.sidebar.page_link(page, label=label)

    st.sidebar.markdown('<div class="sidebar-section">Status</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="font-size:.82rem;color:#cbd5e1;line-height:1.55;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#22c55e;margin-right:7px;"></span>
            Evidence dashboard active<br>
            <span style="color:#94a3b8;">Route exposure ≠ exact sale amount</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


sidebar()

# ==============================
# DATA
# ==============================

master = load_json(MASTER)
bridge = load_json(BRIDGE_INFRA)
metrics = bridge.get("cluster_metrics", {})
terminals = load_csv(TERMINALS)
unclassified = load_csv(UNCLASSIFIED)

analysis = master.get("independent_chain_analysis", {})
missing_cell = analysis.get("deduped_unmatched_cell")
missing_mcell = analysis.get("deduped_unmatched_mcell_equivalent")

wallet_file = MISSING_WALLETS_DEDUPED if MISSING_WALLETS_DEDUPED.exists() else MISSING_WALLETS
wallets = load_csv(wallet_file)

if missing_cell is None and not wallets.empty and "missing_cell" in wallets.columns:
    missing_cell = pd.to_numeric(wallets["missing_cell"], errors="coerce").sum()
    missing_mcell = missing_cell / CELL_PER_MCELL

missing_display = fmt_num(missing_cell) if missing_cell is not None else "—"
missing_mcell_display = fmt_num(missing_mcell) if missing_mcell is not None else "—"

cex_exposure = metrics.get("known_cex_routes_cell_possible", 0)
dex_exposure = metrics.get("known_dex_router_routes_cell_possible", 0)
mev_exposure = metrics.get("known_mev_routes_cell_possible", 0)

# ==============================
# HERO
# ==============================

st.markdown(
    """
<div class="hero">
  <span class="chip chip-green">Updated Evidence Model</span>
  <span class="chip chip-blue">Bridge infrastructure identified</span>
  <span class="chip chip-red">Market-route exposure identified</span>
  <h1>CF20 / CELL Independent Audit</h1>
  <p>
    The audit now identifies bridge lock/unlock infrastructure, bridge intake and aggregator wallets,
    downstream distribution routes, and terminal exposure into CEX, DEX/router, and MEV infrastructure.
    The remaining open question is not whether market routes exist — they do — but how much was ultimately sold
    after routing into exchanges and swap infrastructure.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# ==============================
# KPI ROW
# ==============================

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    metric_card("Deduped unmatched CELL", missing_display, "Independent unmatched-emission estimate", "red")
with k2:
    metric_card("mCELL equivalent", missing_mcell_display, "CELL ÷ 1,000", "orange")
with k3:
    metric_card("Reachable wallets", f"{int(metrics.get('reachable_wallets') or 0):,}", "Bridge-cluster traversal", "blue")
with k4:
    metric_card("Terminal endpoints", f"{int(metrics.get('terminal_endpoint_count') or 0):,}", "CEX / DEX / MEV known endpoints", "green")
with k5:
    metric_card("Unclassified wallets", f"{int(metrics.get('unclassified_wallet_count') or 0):,}", "Remaining label work", "purple")

st.markdown("## What we now know")

c1, c2, c3, c4, c5 = st.columns(5)

cards = [
    ("01", "Lock / Unlock endpoint found", "0xfd64... shows Lock Token and Unlock Token methods and routes to 0x4A831... and 0x35ce....", "chip-green", "Bridge infrastructure"),
    ("02", "Bridge intake identified", "0x4A831... receives Bridge Token calls and routes onward into the bridge cluster.", "chip-blue", "Bridge Token"),
    ("03", "Distribution cluster mapped", "0x35ce..., 0x50ebb..., 0x65def..., 0xd3ec..., 0xda8a..., and related wallets form a multi-hop routing cluster.", "chip-orange", "Downstream routing"),
    ("04", "Market endpoints found", "Traversal reaches Gate.io, MEXC, Uniswap, MetaMask Swaps, 1inch, ParaSwap, CoW, and MEV infrastructure.", "chip-red", "CEX / DEX / MEV"),
    ("05", "Sale amount still not exact", "CEX internal trading is off-chain and graph routes can overlap, so route exposure is not exact realized sale volume.", "chip-purple", "Audit caveat"),
]

for col, (num, title, copy, chip_class, chip) in zip([c1, c2, c3, c4, c5], cards):
    with col:
        st.markdown(
            f"""
<div class="audit-card">
  <div class="audit-card-inner">
    <div class="audit-num">{num}</div>
    <div class="audit-title">{title}</div>
    <div class="audit-copy">{copy}</div>
    <br>
    <span class="chip {chip_class}">{chip}</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown("## Current Bridge Model")

st.markdown(
    """
<div class="flow-wrap">
  <div class="flow-grid">
    <div class="flow-node"><b>0xfd64...</b><br><span>Bridge Lock / Unlock endpoint<br>Methods: Lock Token, Unlock Token</span></div>
    <div class="flow-arrow">→</div>
    <div class="flow-node"><b>0x4A831...</b><br><span>Bridge Token intake / router<br>User-facing bridge calls</span></div>
    <div class="flow-arrow">→</div>
    <div class="flow-node"><b>0x35ce...</b><br><span>Bridge aggregator<br>Routes to distributor wallets</span></div>
    <div class="flow-arrow">→</div>
    <div class="flow-node"><b>0x50ebb / 0x65def / 0xd3ec</b><br><span>Distributor layer<br>Multi-hop routing cluster</span></div>
    <div class="flow-arrow">→</div>
    <div class="flow-node"><b>0xda8a / 0x9c4...</b><br><span>Consolidation / market hub<br>Routes into CEX and DEX</span></div>
    <div class="flow-arrow">→</div>
    <div class="flow-node"><b>Gate.io / MEXC / Uniswap / 1inch</b><br><span>Market infrastructure<br>CEX, DEX/router, MEV endpoints</span></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("## Route Exposure Summary")

r1, r2, r3 = st.columns(3)

with r1:
    metric_card("Known CEX route exposure", f"{float(cex_exposure):,.2f} CELL", "Gate.io / MEXC-labelled endpoints", "red")
with r2:
    metric_card("Known DEX/router exposure", f"{float(dex_exposure):,.2f} CELL", "Uniswap / 1inch / MetaMask / ParaSwap / CoW", "blue")
with r3:
    metric_card("Known MEV exposure", f"{float(mev_exposure):,.2f} CELL", "MEV/searcher-labelled endpoint(s)", "orange")

st.caption("Route exposure means graph-path exposure, not exact final sale volume. Paths can overlap or loop.")

# ==============================
# TERMINALS TABLE
# ==============================

left, right = st.columns([1.1, 1])

with left:
    st.markdown("## Terminal Market Endpoints")
    if terminals.empty:
        st.info("Run `python3 trace_bridge_cluster.py` to generate terminal endpoint data.")
    else:
        show = terminals.copy()
        if "terminal_inflow_possible_cell" in show.columns:
            show["terminal_inflow_possible_cell"] = pd.to_numeric(show["terminal_inflow_possible_cell"], errors="coerce").fillna(0)
            show = show.sort_values("terminal_inflow_possible_cell", ascending=False)
            show["terminal_inflow_possible_cell"] = show["terminal_inflow_possible_cell"].map(lambda x: f"{x:,.2f}")
        cols = [c for c in ["label", "class", "address", "terminal_inflow_possible_cell", "paths"] if c in show.columns]
        st.dataframe(show[cols].head(20), use_container_width=True, hide_index=True)

with right:
    st.markdown("## Evidence Status")
    status_rows = pd.DataFrame([
        {"Finding": "Bridge lock/unlock infrastructure", "Status": "Identified", "Evidence": "0xfd64... Lock Token / Unlock Token"},
        {"Finding": "Bridge intake/router", "Status": "Identified", "Evidence": "0x4A831... Bridge Token calls"},
        {"Finding": "Downstream distribution cluster", "Status": "Mapped", "Evidence": "0x35ce → 0x50ebb / 0x65def / 0xd3ec / 0xda8a"},
        {"Finding": "CEX route exposure", "Status": "Identified", "Evidence": "Gate.io / MEXC terminal endpoints"},
        {"Finding": "DEX/router exposure", "Status": "Identified", "Evidence": "Uniswap / 1inch / MetaMask / ParaSwap / CoW"},
        {"Finding": "Exact realized sale proceeds", "Status": "Unresolved", "Evidence": "CEX internal trades are off-chain; DEX swaps require tx-level log verification"},
        {"Finding": "Full reserve reconciliation", "Status": "Unresolved", "Evidence": "Bridge infrastructure found, but backing reconciliation still requires lock/reserve accounting"},
    ])
    st.dataframe(status_rows, use_container_width=True, hide_index=True)

# ==============================
# CHART
# ==============================

if not terminals.empty and {"label", "class", "terminal_inflow_possible_cell"}.issubset(terminals.columns):
    chart_df = terminals.copy()
    chart_df["terminal_inflow_possible_cell"] = pd.to_numeric(chart_df["terminal_inflow_possible_cell"], errors="coerce").fillna(0)
    chart_df = chart_df.sort_values("terminal_inflow_possible_cell", ascending=False).head(12)
    chart_df["endpoint"] = chart_df["label"].fillna("") + " (" + chart_df["class"].fillna("") + ")"

    st.markdown("## Market Endpoint Route Exposure")
    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("terminal_inflow_possible_cell:Q", title="Route exposure possible CELL"),
            y=alt.Y("endpoint:N", title=None, sort="-x"),
            tooltip=[
                alt.Tooltip("label:N", title="Endpoint"),
                alt.Tooltip("class:N", title="Class"),
                alt.Tooltip("terminal_inflow_possible_cell:Q", title="Possible CELL exposure", format=",.2f"),
                alt.Tooltip("address:N", title="Address"),
            ],
        )
        .properties(height=430)
    )
    st.altair_chart(chart, use_container_width=True)

# ==============================
# DOWNLOADS
# ==============================

st.markdown("## Core Evidence Downloads")

downloads = [
    ("Bridge Infrastructure Summary", BRIDGE_INFRA, "application/json"),
    ("Bridge Cluster Summary", Path("bridge_cluster_summary.json"), "application/json"),
    ("Terminal Endpoints", TERMINALS, "text/csv"),
    ("Unclassified Wallets", UNCLASSIFIED, "text/csv"),
    ("Wallet Label Priority Review", Path("wallet_label_priority_review.csv"), "text/csv"),
    ("Known Wallet Labels", Path("known_wallet_labels.csv"), "text/csv"),
]

cols = st.columns(3)
for i, (label, path, mime) in enumerate(downloads):
    with cols[i % 3]:
        if path.exists():
            st.download_button(label, path.read_bytes(), file_name=path.name, mime=mime, use_container_width=True)
        else:
            st.caption(f"Missing: {path.name}")

st.warning(
    "Audit caveat: route-exposure totals are not exact final sale amounts. "
    "They identify paths into market infrastructure. CEX deposits prove exchange custody routing, "
    "but exchange-internal trades are off-chain."
)
