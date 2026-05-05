import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="CF20 Audit | No Verifiable Lock Contract",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# FILES / CONFIG
# =============================

MASTER = Path("audit_master_summary.json")
MISSING_WALLETS_DEDUPED = Path("missing_cell_wallets_deduped.csv")
MISSING_WALLETS = Path("missing_cell_wallets.csv")
BRIDGE_IMAGE = Path("assets/no_verifiable_lock_contract.png")

CELL_PER_MCELL = 1000


# =============================
# HELPERS
# =============================

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
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:,.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:,.2f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:,.2f}K"
    return f"{n:,.2f}"


def short_wallet(w):
    w = str(w)
    if len(w) <= 16:
        return w
    return w[:10] + "..." + w[-6:]


def sidebar():
    st.sidebar.markdown(
        """
        <div class="sidebar-brand-wrap">
            <div class="sidebar-badge">🛡️</div>
            <div class="sidebar-brand-text">CF20 Audit</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="sidebar-section">Main</div>', unsafe_allow_html=True)
    st.sidebar.page_link("app.py", label="Home / Verdict")

    st.sidebar.markdown('<div class="sidebar-section">Evidence</div>', unsafe_allow_html=True)

    page_links = [
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
        <div class="status-small">
            <span class="green-dot"></span>Dashboard active<br>
            <span class="muted">Independent audit mode enabled</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(label, value, sub="", color_class=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value {color_class}">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================
# CSS
# =============================

st.markdown(
    """
<style>
html, body, [class*="css"] {
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 18% 10%, rgba(59,130,246,0.18), transparent 24%),
        radial-gradient(circle at 82% 10%, rgba(239,68,68,0.12), transparent 22%),
        radial-gradient(circle at 50% 90%, rgba(34,197,94,0.08), transparent 22%),
        #040b16;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07101d 0%, #06111f 100%);
    border-right: 1px solid rgba(148,163,184,0.16);
}

[data-testid="stSidebar"] * {
    color: #dbeafe;
}

.block-container {
    max-width: 1650px;
    padding-top: 0.85rem;
    padding-left: 1.1rem;
    padding-right: 1.1rem;
}

#MainMenu, header, footer {
    visibility: hidden;
}

.sidebar-brand-wrap {
    display:flex;
    align-items:center;
    gap:10px;
    margin: 8px 0 14px 0;
}

.sidebar-badge {
    width:34px;
    height:34px;
    border-radius:10px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:1.1rem;
    border:1px solid rgba(96,165,250,0.25);
    background:linear-gradient(145deg, rgba(37,99,235,0.22), rgba(168,85,247,0.18));
    box-shadow:0 0 14px rgba(59,130,246,0.18);
}

.sidebar-brand-text {
    font-size: 1.08rem;
    font-weight: 900;
    color: #f8fafc;
}

.sidebar-section {
    color: #94a3b8;
    font-size: 0.72rem;
    font-weight: 800;
    margin: 18px 0 6px 0;
    text-transform: uppercase;
}

.green-dot {
    display:inline-block;
    width:8px;
    height:8px;
    border-radius:50%;
    background:#22c55e;
    margin-right:7px;
}

.status-small {
    color:#cbd5e1;
    font-size:.82rem;
    line-height:1.5;
}

.muted {
    color:#94a3b8;
}

.hero {
    border: 1px solid rgba(59,130,246,0.26);
    background:
        linear-gradient(145deg, rgba(6,18,34,0.96), rgba(8,16,28,0.94));
    border-radius: 18px;
    padding: 18px 22px 16px 22px;
    box-shadow: 0 18px 50px rgba(0,0,0,0.28);
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
}

.hero:before {
    content:"";
    position:absolute;
    top:0;
    left:0;
    right:0;
    height:2px;
    background:linear-gradient(90deg, rgba(96,165,250,0.0), rgba(96,165,250,0.95), rgba(96,165,250,0.0));
}

.hero-title {
    font-size: 2.75rem;
    font-weight: 900;
    color: #f8fafc;
    line-height: 1.04;
    letter-spacing: -0.03em;
    margin-bottom: 6px;
    text-transform: uppercase;
}

.hero-sub {
    font-size: 1.15rem;
    color: #60a5fa;
    font-weight: 800;
    margin-bottom: 12px;
}

.hero-copy {
    color: #cbd5e1;
    line-height: 1.65;
    font-size: 0.97rem;
}

.unit-note {
    border: 1px solid rgba(56,189,248,0.25);
    background: rgba(7,18,34,0.65);
    border-radius: 14px;
    padding: 12px 14px;
    color: #cbd5e1;
    line-height: 1.55;
    margin-bottom: 14px;
}

.section-heading {
    color: #f8fafc;
    font-size: 1.4rem;
    font-weight: 900;
    margin: 16px 0 10px 0;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.status-chip-row {
    display:flex;
    gap:10px;
    flex-wrap:wrap;
    margin: 8px 0 14px 0;
}

.status-chip {
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding: 8px 12px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 0.78rem;
    border:1px solid rgba(148,163,184,0.22);
    background: rgba(8,18,34,0.80);
    color:#dbeafe;
    box-shadow: 0 0 14px rgba(59,130,246,0.08);
}

.status-chip.blue {
    border-color: rgba(59,130,246,0.35);
    color:#93c5fd;
    box-shadow: 0 0 14px rgba(59,130,246,0.18);
}

.status-chip.green {
    border-color: rgba(34,197,94,0.35);
    color:#86efac;
    box-shadow: 0 0 14px rgba(34,197,94,0.14);
}

.status-chip.orange {
    border-color: rgba(245,158,11,0.35);
    color:#fcd34d;
    box-shadow: 0 0 14px rgba(245,158,11,0.14);
}

.status-chip.red {
    border-color: rgba(239,68,68,0.42);
    color:#fca5a5;
    box-shadow: 0 0 14px rgba(239,68,68,0.16);
}

.kpi-card {
    border: 1px solid rgba(148,163,184,0.18);
    background: linear-gradient(145deg, rgba(15,23,42,.96), rgba(12,28,50,.88));
    border-radius: 14px;
    padding: 16px;
    min-height: 126px;
    box-shadow: 0 18px 40px rgba(0,0,0,0.24);
    position:relative;
    overflow:hidden;
}

.kpi-card:before {
    content:"";
    position:absolute;
    top:0;
    left:0;
    right:0;
    height:2px;
    background:linear-gradient(90deg, rgba(255,255,255,0), rgba(96,165,250,0.7), rgba(255,255,255,0));
}

.kpi-label {
    color: #cbd5e1;
    font-size: 0.84rem;
    font-weight: 700;
    margin-bottom: 8px;
}

.kpi-value {
    color: #f8fafc;
    font-size: 1.55rem;
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: -0.03em;
}

.kpi-sub {
    color: #94a3b8;
    font-size: 0.8rem;
    font-weight: 700;
    margin-top: 8px;
    line-height: 1.4;
}

.red-text { color: #f87171 !important; }
.orange-text { color: #f59e0b !important; }
.green-text { color: #4ade80 !important; }
.blue-text { color: #60a5fa !important; }
.purple-text { color: #c084fc !important; }

.infographic-panel {
    border-radius: 18px;
    padding: 16px;
    min-height: 100%;
    border:1px solid rgba(148,163,184,0.18);
    background: linear-gradient(145deg, rgba(11,20,35,0.96), rgba(8,16,29,0.94));
    box-shadow: 0 18px 40px rgba(0,0,0,.22);
}

.infographic-panel.blue {
    border-color: rgba(59,130,246,0.35);
}

.infographic-panel.red {
    border-color: rgba(239,68,68,0.35);
}

.panel-title {
    font-size: 1.55rem;
    font-weight: 900;
    color: #f8fafc;
    margin-bottom: 4px;
    text-transform: uppercase;
    text-align:center;
}

.panel-subtitle {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-bottom: 12px;
    text-align:center;
}

.flow-track-3 {
    display:grid;
    grid-template-columns: 1fr 58px 1fr 58px 1fr;
    gap: 8px;
    align-items:center;
    margin-top: 4px;
}

.flow-track-4 {
    display:grid;
    grid-template-columns: 1fr 52px 1fr 52px 1fr 52px 1fr;
    gap: 8px;
    align-items:center;
    margin-top: 4px;
}

.flow-node {
    border-radius: 16px;
    padding: 14px 12px;
    min-height: 132px;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    flex-direction:column;
    font-weight:800;
    line-height:1.35;
    position:relative;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
}

.flow-node .node-title {
    font-size: 1.3rem;
    font-weight: 900;
    color: #f8fafc;
    margin-bottom: 6px;
}

.flow-node .node-copy {
    font-size: 0.84rem;
    font-weight: 700;
    color:#dbeafe;
    line-height:1.5;
}

.flow-node.purple {
    border:1px solid rgba(168,85,247,0.55);
    background:linear-gradient(145deg, rgba(43,18,67,0.72), rgba(16,16,35,0.65));
    box-shadow: 0 0 18px rgba(168,85,247,0.18);
}

.flow-node.green {
    border:1px solid rgba(34,197,94,0.55);
    background:linear-gradient(145deg, rgba(10,50,28,0.72), rgba(16,16,35,0.65));
    box-shadow: 0 0 18px rgba(34,197,94,0.18);
}

.flow-node.blue {
    border:1px solid rgba(59,130,246,0.55);
    background:linear-gradient(145deg, rgba(8,38,70,0.72), rgba(16,16,35,0.65));
    box-shadow: 0 0 18px rgba(59,130,246,0.18);
}

.flow-node.red {
    border:1px solid rgba(239,68,68,0.60);
    background:linear-gradient(145deg, rgba(65,14,14,0.78), rgba(16,16,35,0.68));
    box-shadow: 0 0 20px rgba(239,68,68,0.22);
}

.flow-node.orange {
    border:1px solid rgba(249,115,22,0.58);
    background:linear-gradient(145deg, rgba(66,26,8,0.78), rgba(16,16,35,0.68));
    box-shadow: 0 0 20px rgba(249,115,22,0.18);
}

.flow-arrow {
    text-align:center;
    font-size: 2.25rem;
    font-weight: 900;
    color:#60a5fa;
    text-shadow:0 0 12px rgba(96,165,250,0.75), 0 0 28px rgba(96,165,250,0.35);
}

.flow-arrow.red {
    color:#f87171;
    text-shadow:0 0 12px rgba(248,113,113,0.75), 0 0 28px rgba(248,113,113,0.35);
}

.flow-stack {
    display:grid;
    gap:8px;
}

.flow-mini {
    border-radius: 12px;
    padding: 10px 8px;
    text-align:center;
    min-height:58px;
    border:1px solid rgba(59,130,246,0.45);
    background: rgba(8,28,46,0.78);
    color:#dbeafe;
    font-weight:800;
    box-shadow:0 0 12px rgba(59,130,246,0.14);
}

.audit-alert {
    border: 1px solid rgba(239,68,68,0.45);
    background: rgba(40,10,10,0.35);
    color: #fecaca;
    padding: 12px 14px;
    border-radius: 12px;
    font-weight: 700;
    margin-top: 12px;
    line-height:1.55;
}

.audit-card {
    border:1px solid rgba(148,163,184,0.18);
    border-radius:16px;
    padding:18px 16px 16px 16px;
    background: linear-gradient(145deg, rgba(11,20,35,0.96), rgba(9,16,29,0.94));
    box-shadow: 0 18px 36px rgba(0,0,0,.22);
    min-height: 245px;
    position:relative;
    overflow:hidden;
}

.audit-card.purple { border-color: rgba(168,85,247,0.42); }
.audit-card.blue { border-color: rgba(59,130,246,0.42); }
.audit-card.green { border-color: rgba(45,212,191,0.42); }
.audit-card.orange { border-color: rgba(249,115,22,0.42); }

.audit-number {
    position:absolute;
    top:12px;
    left:12px;
    width:32px;
    height:32px;
    border-radius:10px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:900;
    color:#f8fafc;
    border:1px solid rgba(255,255,255,0.18);
    background: rgba(8,16,28,0.70);
    box-shadow: 0 0 12px rgba(96,165,250,0.15);
}

.audit-icon {
    width:72px;
    height:72px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    margin: 20px auto 14px auto;
    font-size: 2rem;
    font-weight: 900;
    border:1px solid rgba(255,255,255,0.12);
}

.audit-card.purple .audit-icon {
    color:#d8b4fe;
    background: rgba(120,38,182,0.18);
    box-shadow:0 0 18px rgba(168,85,247,0.18);
}
.audit-card.blue .audit-icon {
    color:#93c5fd;
    background: rgba(37,99,235,0.18);
    box-shadow:0 0 18px rgba(59,130,246,0.18);
}
.audit-card.green .audit-icon {
    color:#99f6e4;
    background: rgba(13,148,136,0.18);
    box-shadow:0 0 18px rgba(45,212,191,0.18);
}
.audit-card.orange .audit-icon {
    color:#fdba74;
    background: rgba(234,88,12,0.18);
    box-shadow:0 0 18px rgba(249,115,22,0.18);
}

.audit-title {
    color:#f8fafc;
    font-size:1.45rem;
    font-weight:900;
    line-height:1.22;
    margin-bottom:8px;
    text-align:left;
}

.audit-copy {
    color:#cbd5e1;
    font-size:0.96rem;
    line-height:1.62;
}

.indicator-panel {
    border:1px solid rgba(59,130,246,0.22);
    background: linear-gradient(145deg, rgba(8,16,28,0.95), rgba(7,14,24,0.93));
    border-radius: 16px;
    padding: 16px;
}

.indicator-pill {
    border:1px solid rgba(59,130,246,0.30);
    background: rgba(7,18,32,0.82);
    border-radius: 14px;
    padding: 16px 12px;
    min-height: 72px;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    color:#dbeafe;
    font-weight:800;
    box-shadow:0 0 14px rgba(59,130,246,0.10);
}

.indicator-pill.red {
    border-color: rgba(239,68,68,0.35);
    color:#fecaca;
    box-shadow:0 0 14px rgba(239,68,68,0.12);
}

.subpanel {
    border:1px solid rgba(148,163,184,0.18);
    background: linear-gradient(145deg, rgba(12,20,34,0.95), rgba(8,16,28,0.93));
    border-radius: 16px;
    padding: 16px;
    min-height: 100%;
    box-shadow: 0 18px 36px rgba(0,0,0,.18);
}

.subpanel-title {
    color:#f8fafc;
    font-size:1.2rem;
    font-weight:900;
    margin-bottom:10px;
    text-transform:uppercase;
}

.bridge-bullets {
    color:#cbd5e1;
    line-height:1.72;
    font-size:0.96rem;
}

.bridge-bullets code {
    color:#93c5fd;
    background: rgba(15,23,42,0.92);
    padding:2px 6px;
    border-radius:6px;
}

.conclusion {
    border: 1px solid rgba(239,68,68,0.42);
    background: linear-gradient(145deg, rgba(48,12,12,0.52), rgba(18,12,18,0.72));
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: 0 18px 40px rgba(0,0,0,.22);
}

.conclusion-title {
    color: #fb7185;
    font-size: 2.1rem;
    font-weight: 900;
    line-height: 1.22;
    text-transform: uppercase;
}

.conclusion-copy {
    color: #fecaca;
    font-size: 1.02rem;
    line-height: 1.75;
    margin-top: 10px;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# LOAD DATA
# =============================

sidebar()

master = load_json(MASTER)
analysis = master.get("independent_chain_analysis", {})
official = master.get("official_disclosure", {})
bridge = master.get("bridge_out_evidence", {})
market = master.get("market_sale_quantification", {})

wallet_file = MISSING_WALLETS_DEDUPED if MISSING_WALLETS_DEDUPED.exists() else MISSING_WALLETS
wallets = load_csv(wallet_file)

missing_cell = analysis.get("deduped_unmatched_cell")
missing_mcell = analysis.get("deduped_unmatched_mcell_equivalent")
duplicate_count = analysis.get("event_duplicates_removed")
top5_share = analysis.get("top5_share_percent")

official_mcell = official.get("illegal_mcell", 1295)
official_cell = official.get("cell_equivalent", official_mcell * CELL_PER_MCELL)

if missing_cell is None and not wallets.empty and "missing_cell" in wallets.columns:
    missing_cell = pd.to_numeric(wallets["missing_cell"], errors="coerce").sum()

if missing_mcell is None and missing_cell is not None:
    missing_mcell = missing_cell / CELL_PER_MCELL

if top5_share is None and not wallets.empty and "missing_cell" in wallets.columns:
    total = pd.to_numeric(wallets["missing_cell"], errors="coerce").sum()
    top5 = pd.to_numeric(wallets["missing_cell"], errors="coerce").head(5).sum()
    top5_share = (top5 / total * 100) if total else None

missing_display = fmt_num(missing_cell) if missing_cell is not None else "15.75M"
missing_mcell_display = fmt_num(missing_mcell) if missing_mcell is not None else "15.75K"
top5_display = f"{top5_share:,.2f}%" if top5_share is not None else "67.67%"
duplicate_display = f"{duplicate_count:,}" if duplicate_count is not None else "—"

bridge_found = bridge.get("found", True)
bridge_status = "Bridge-out evidence found" if bridge_found else "Bridge-out evidence not loaded"
market_status = market.get("status", "Unresolved")

source_wallet_short = bridge.get("source_wallet_short", "Rj7J7...MLE7o7T")
bep20_destination = bridge.get("bep20_destination", "0x1fa6348d9b13d316c62d54f62bea4e1a7207d9d6")
bridge_condition_value = bridge.get("bridge_condition_value_cell", 3876436.277)
datum_type = bridge.get("datum_type", "DATUM_TX")


# =============================
# HERO
# =============================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">CF20 Bridge Audit Finding: No Verifiable Lock Contract</div>
        <div class="hero-sub">Why backing remains unproven on Ethereum and BSC</div>
        <div class="hero-copy">
            This homepage is designed as an independent audit command view. It focuses on what can be verified from
            current evidence: observable ETH/BSC supply, unmatched issuance analysis, bridge-out indicators, and whether
            a publicly verifiable reserve / lock / burn path can be independently proven.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="unit-note">
        <b>Unit note:</b> 1 mCELL = 1,000 CELL.<br>
        Independent deduped result: <b>{missing_mcell_display} mCELL-equivalent</b> / <b>{missing_display} CELL</b>.<br>
        Official disclosure reference: <b>{official_mcell:,} mCELL</b> / <b>{official_cell:,.0f} CELL-equivalent</b>.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="status-chip-row">
        <div class="status-chip blue">🔹 ETH contract observed</div>
        <div class="status-chip blue">🔹 BSC contract observed</div>
        <div class="status-chip green">✅ {bridge_status}</div>
        <div class="status-chip orange">⚠ Market quantification: {market_status}</div>
        <div class="status-chip red">⛔ No public reserve lock verified</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# KPI ROW
# =============================

k1, k2, k3, k4, k5 = st.columns(5, gap="large")

with k1:
    render_kpi("Deduped unmatched CELL", missing_display, "Independent chain analysis", "red-text")
with k2:
    render_kpi("mCELL equivalent", missing_mcell_display, "CELL ÷ 1,000", "orange-text")
with k3:
    render_kpi("Official illegal mCELL", f"{official_mcell:,}", "Referenced official disclosure", "purple-text")
with k4:
    render_kpi("Top 5 concentration", top5_display, "Share of unmatched recipient total", "blue-text")
with k5:
    render_kpi("Duplicate events removed", duplicate_display, "Audit master summary", "green-text")

# =============================
# INFOGRAPHIC CENTER SECTION
# =============================

st.markdown('<div class="section-heading">Bridge Model vs Audit Finding</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown(
        """
        <div class="infographic-panel blue">
            <div class="panel-title">Expected Bridge Model</div>
            <div class="panel-subtitle">What should exist for transparent reserve-backed bridging</div>

            <div class="flow-track-3">
                <div class="flow-node purple">
                    <div class="node-title">Zerochain<br>/ mints</div>
                    <div class="node-copy">Source-side issuance or bridge event begins the process.</div>
                </div>
                <div class="flow-arrow">➜</div>
                <div class="flow-node green">
                    <div class="node-title">Verifiable lock /<br>reserve custody</div>
                    <div class="node-copy">Should prove backing CELL is locked, burned, or transparently custodied.</div>
                </div>
                <div class="flow-arrow">➜</div>
                <div class="flow-node blue">
                    <div class="node-title">ETH / BSC<br>token supply</div>
                    <div class="node-copy">External-chain supply appears only alongside provable reserve logic.</div>
                </div>
            </div>

            <div class="audit-alert" style="border-color:rgba(34,197,94,0.35); background:rgba(8,40,20,0.25); color:#bbf7d0;">
                Expected outcome: the bridge should publicly prove where the backing sits and how it is secured.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="infographic-panel red">
            <div class="panel-title">What the Audit Found</div>
            <div class="panel-subtitle">What current independent evidence supports</div>

            <div class="flow-track-4">
                <div class="flow-node purple">
                    <div class="node-title">Zerochain<br>emissions</div>
                    <div class="node-copy">Emission activity and related bridge evidence can be observed.</div>
                </div>
                <div class="flow-arrow red">➜</div>
                <div class="flow-node red">
                    <div class="node-title">No identified<br>lock contract</div>
                    <div class="node-copy">No discoverable lock, reserve, or burn contract was independently verified.</div>
                </div>
                <div class="flow-arrow red">➜</div>
                <div class="flow-stack">
                    <div class="flow-mini">ETH<br>contract</div>
                    <div class="flow-mini">BSC<br>contract</div>
                </div>
                <div class="flow-arrow red">➜</div>
                <div class="flow-node blue">
                    <div class="node-title">Exchanges /<br>LP / wallets</div>
                    <div class="node-copy">Circulating external-chain activity exists, but reserve proof remains incomplete.</div>
                </div>
            </div>

            <div class="audit-alert">
                No verifiable on-chain lock, burn, or reserve contract found. Tokens may circulate on ETH/BSC without a publicly provable reserve path.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
if BRIDGE_IMAGE.exists():
    st.image(str(BRIDGE_IMAGE), use_container_width=True)
else:
    st.warning("Image not found: assets/no_verifiable_lock_contract.png")

# =============================
# NUMBERED AUDIT CARDS
# =============================

st.markdown('<div class="section-heading">Key Audit Findings</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4, gap="large")

with c1:
    st.markdown(
        """
        <div class="audit-card purple">
            <div class="audit-number">1</div>
            <div class="audit-icon">⌕</div>
            <div class="audit-title">No lock contract located</div>
            <div class="audit-copy">
                No verifiable reserve-holding lock contract was identified for the bridged supply.
                The audit could not independently confirm a canonical on-chain reserve location.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="audit-card blue">
            <div class="audit-number">2</div>
            <div class="audit-icon">⌘</div>
            <div class="audit-title">No confirmed custody wallet</div>
            <div class="audit-copy">
                No clearly disclosed reserve multisig or custody wallet was confirmed as the backing holder.
                Without a named reserve address, backing cannot be independently verified.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="audit-card green">
            <div class="audit-number">3</div>
            <div class="audit-icon">◈</div>
            <div class="audit-title">Supply exists on ETH/BSC</div>
            <div class="audit-copy">
                CF20/CELL-related supply is observable on Ethereum and BSC, including exchange and LP balances.
                Observable circulating supply is not the same thing as provable reserve backing.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        """
        <div class="audit-card orange">
            <div class="audit-number">4</div>
            <div class="audit-icon">⚠</div>
            <div class="audit-title">Backing gap remains unresolved</div>
            <div class="audit-copy">
                Without a discoverable lock, reserve, or burn mechanism, proof of 1:1 backing remains incomplete.
                The audit therefore treats backing as unverified rather than proven.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================
# INDICATORS
# =============================

st.markdown('<div class="section-heading">Observed On-Chain Indicators</div>', unsafe_allow_html=True)

st.markdown('<div class="indicator-panel">', unsafe_allow_html=True)
i1, i2, i3, i4, i5 = st.columns(5, gap="medium")

with i1:
    st.markdown('<div class="indicator-pill">ETH contract observed</div>', unsafe_allow_html=True)
with i2:
    st.markdown('<div class="indicator-pill">BSC contract observed</div>', unsafe_allow_html=True)
with i3:
    st.markdown('<div class="indicator-pill">Exchange and LP balances observed</div>', unsafe_allow_html=True)
with i4:
    st.markdown('<div class="indicator-pill">Bridge-out activity observed</div>', unsafe_allow_html=True)
with i5:
    st.markdown('<div class="indicator-pill red">No reserve lock address verified</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =============================
# LOWER PANELS
# =============================

left2, right2 = st.columns([1.25, 1], gap="large")

with left2:
    st.markdown('<div class="subpanel-title">Top Unmatched Recipients</div>', unsafe_allow_html=True)
    if wallets.empty:
        st.info("missing_cell_wallets_deduped.csv or missing_cell_wallets.csv not found.")
    else:
        show = wallets.copy().head(10)

        if "mint_to" in show.columns:
            show["wallet_short"] = show["mint_to"].apply(short_wallet)

        if "missing_cell" in show.columns:
            show["missing_cell_num"] = pd.to_numeric(show["missing_cell"], errors="coerce")
            show["missing_mcell_equivalent"] = show["missing_cell_num"] / CELL_PER_MCELL
            show["missing_cell"] = show["missing_cell_num"].map(lambda x: f"{x:,.2f}" if pd.notnull(x) else "—")
            show["missing_mcell_equivalent"] = show["missing_mcell_equivalent"].map(lambda x: f"{x:,.2f}" if pd.notnull(x) else "—")

        if "share_of_missing" in show.columns:
            show["share_of_missing"] = pd.to_numeric(show["share_of_missing"], errors="coerce").map(
                lambda x: f"{x:,.2f}%" if pd.notnull(x) else "—"
            )

        preferred_cols = [c for c in [
            "wallet_short",
            "mint_to",
            "missing_cell",
            "missing_mcell_equivalent",
            "share_of_missing",
            "events",
            "max_single",
            "first",
            "last",
        ] if c in show.columns]

        st.dataframe(
            show[preferred_cols] if preferred_cols else show,
            use_container_width=True,
            hide_index=True,
        )

with right2:
    st.markdown('<div class="subpanel-title">Bridge-Out Evidence</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="subpanel">
            <div class="bridge-bullets">
                <b>Largest unmatched wallet:</b> <code>{source_wallet_short}</code><br><br>
                <b>Observed transaction type:</b> <code>{datum_type}</code> · <code>BRIDGE</code> · <code>OUT</code> · <code>BEP20</code><br><br>
                <b>BEP20 destination:</b> <code>{bep20_destination}</code><br><br>
                <b>Bridge condition value:</b> <code>{bridge_condition_value:,.2f} CELL</code><br><br>
                <b>Status:</b> external-chain destination identified; BSC / DEX / OTC sale path still unresolved.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================
# CONCLUSION
# =============================

st.markdown('<div class="section-heading">Conclusion</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="conclusion">
        <div class="conclusion-title">
            Conclusion: the audit did not verify a lock contract, reserve contract, or fully provable on-chain backing path.
        </div>
        <div class="conclusion-copy">
            Tokens on ETH/BSC may circulate without a publicly verifiable locked reserve.
            The independent audit therefore treats backing as <b>unproven</b>, not proven.
            <br><br>
            Current independent deduped result: <b>{missing_display} CELL</b> / <b>{missing_mcell_display} mCELL-equivalent</b>.
            Until a verifiable reserve mechanism is disclosed and independently confirmed, the backing gap remains unresolved.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# DOWNLOADS
# =============================

st.markdown('<div class="section-heading">Evidence Downloads</div>', unsafe_allow_html=True)

download_files = [
    ("Audit Master Summary", "audit_master_summary.json"),
    ("Deduped Missing CELL Wallets", "missing_cell_wallets_deduped.csv"),
    ("Deduped Missing CELL Events", "missing_cell_events_deduped.csv"),
    ("Evidence Hashes", "evidence_hashes.csv"),
    ("Missing CELL Wallets", "missing_cell_wallets.csv"),
    ("Missing CELL Events", "missing_cell_events.csv"),
    ("Mint Cross-Check", "cf20_mint_crosscheck.csv"),
    ("Bridge-Out Activity Raw", "zerochain_missing_cell_activity_raw.csv"),
]

d1, d2 = st.columns(2, gap="large")

with d1:
    for label, filename in download_files[:4]:
        p = Path(filename)
        if p.exists():
            st.download_button(
                f"Download {label}",
                data=p.read_bytes(),
                file_name=filename,
                mime="text/csv" if filename.endswith(".csv") else "application/json",
                use_container_width=True,
            )
        else:
            st.caption(f"Missing: {filename}")

with d2:
    for label, filename in download_files[4:]:
        p = Path(filename)
        if p.exists():
            st.download_button(
                f"Download {label}",
                data=p.read_bytes(),
                file_name=filename,
                mime="text/csv" if filename.endswith(".csv") else "application/json",
                use_container_width=True,
            )
        else:
            st.caption(f"Missing: {filename}")
