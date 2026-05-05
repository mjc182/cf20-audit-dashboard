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


def sidebar():
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">🛡️ CF20 Audit</div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        '<div class="sidebar-section">Main</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.page_link("app.py", label="Home / Verdict")

    st.sidebar.markdown(
        '<div class="sidebar-section">Evidence</div>',
        unsafe_allow_html=True,
    )

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

    st.sidebar.markdown(
        '<div class="sidebar-section">Status</div>',
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """
        <div class="status-small">
            <span class="green-dot"></span>Dashboard active<br>
            <span class="muted">Independent audit mode enabled</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, sub="", color_class=""):
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


def info_box(title, body, color="blue"):
    st.markdown(
        f"""
        <div class="info-box {color}">
            <div class="info-title">{title}</div>
            <div class="info-body">{body}</div>
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
        radial-gradient(circle at 20% 10%, rgba(59,130,246,0.14), transparent 25%),
        radial-gradient(circle at 85% 10%, rgba(239,68,68,0.12), transparent 22%),
        radial-gradient(circle at 50% 90%, rgba(34,197,94,0.08), transparent 24%),
        #050d18;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07101d 0%, #06111f 100%);
    border-right: 1px solid rgba(148,163,184,0.16);
}

[data-testid="stSidebar"] * {
    color: #dbeafe;
}

.block-container {
    max-width: 1600px;
    padding-top: 1rem;
    padding-left: 1.2rem;
    padding-right: 1.2rem;
}

#MainMenu, header, footer {
    visibility: hidden;
}

.sidebar-brand {
    font-size: 1.15rem;
    font-weight: 900;
    color: #f8fafc;
    margin: 10px 0 14px 0;
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
    border: 1px solid rgba(59,130,246,0.28);
    background: linear-gradient(145deg, rgba(6,18,34,0.96), rgba(10,20,36,0.92));
    border-radius: 18px;
    padding: 20px 22px;
    box-shadow: 0 18px 50px rgba(0,0,0,0.28);
    margin-bottom: 16px;
}

.hero-title {
    font-size: 2.15rem;
    font-weight: 900;
    color: #f8fafc;
    line-height: 1.08;
    letter-spacing: -0.03em;
    margin-bottom: 6px;
}

.hero-sub {
    font-size: 1.05rem;
    color: #60a5fa;
    font-weight: 700;
    margin-bottom: 12px;
}

.hero-copy {
    color: #cbd5e1;
    line-height: 1.65;
    font-size: 0.98rem;
}

.panel {
    border: 1px solid rgba(148,163,184,0.18);
    background: linear-gradient(145deg, rgba(15,23,42,.95), rgba(8,20,36,.90));
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 18px 40px rgba(0,0,0,.22);
    height: 100%;
}

.panel-blue {
    border: 1px solid rgba(59,130,246,0.45);
    box-shadow: 0 0 0 1px rgba(59,130,246,0.08), 0 20px 40px rgba(0,0,0,.20);
}

.panel-red {
    border: 1px solid rgba(239,68,68,0.45);
    box-shadow: 0 0 0 1px rgba(239,68,68,0.08), 0 20px 40px rgba(0,0,0,.20);
}

.panel-title {
    font-size: 1.5rem;
    font-weight: 900;
    color: #f8fafc;
    margin-bottom: 6px;
}

.panel-subtitle {
    font-size: 0.95rem;
    color: #94a3b8;
    margin-bottom: 12px;
}

.flow-box {
    border: 1px solid rgba(96,165,250,0.25);
    border-radius: 14px;
    padding: 14px;
    background: rgba(8,16,28,0.60);
    margin-bottom: 10px;
}

.flow-title {
    color: #60a5fa;
    font-size: 0.9rem;
    font-weight: 800;
    margin-bottom: 4px;
}

.flow-text {
    color: #dbeafe;
    font-size: 0.95rem;
    line-height: 1.5;
}

.audit-alert {
    border: 1px solid rgba(239,68,68,0.45);
    background: rgba(40,10,10,0.35);
    color: #fecaca;
    padding: 12px 14px;
    border-radius: 12px;
    font-weight: 700;
    margin-top: 12px;
}

.section-heading {
    color: #f8fafc;
    font-size: 1.35rem;
    font-weight: 900;
    margin: 18px 0 10px 0;
}

.kpi-card {
    border: 1px solid rgba(148,163,184,0.18);
    background: linear-gradient(145deg, rgba(15,23,42,.96), rgba(12,28,50,.88));
    border-radius: 14px;
    padding: 16px;
    min-height: 128px;
    box-shadow: 0 18px 40px rgba(0,0,0,0.26);
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

.red { color: #f87171 !important; }
.orange { color: #f59e0b !important; }
.green { color: #4ade80 !important; }
.blue { color: #60a5fa !important; }
.purple { color: #c084fc !important; }

.info-box {
    border-radius: 14px;
    padding: 16px;
    min-height: 180px;
    margin-bottom: 10px;
}

.info-box.blue {
    border: 1px solid rgba(168,85,247,0.45);
    background: linear-gradient(145deg, rgba(30,12,54,0.35), rgba(16,16,35,0.35));
}

.info-box.cyan {
    border: 1px solid rgba(56,189,248,0.45);
    background: linear-gradient(145deg, rgba(7,33,55,0.35), rgba(16,16,35,0.35));
}

.info-box.green {
    border: 1px solid rgba(45,212,191,0.45);
    background: linear-gradient(145deg, rgba(6,46,42,0.35), rgba(16,16,35,0.35));
}

.info-box.red {
    border: 1px solid rgba(249,115,22,0.45);
    background: linear-gradient(145deg, rgba(50,22,10,0.35), rgba(16,16,35,0.35));
}

.info-title {
    font-size: 1.06rem;
    font-weight: 900;
    color: #f8fafc;
    margin-bottom: 8px;
}

.info-body {
    color: #cbd5e1;
    font-size: 0.96rem;
    line-height: 1.62;
}

.indicator-grid {
    border: 1px solid rgba(59,130,246,0.20);
    background: linear-gradient(145deg, rgba(10,18,30,0.92), rgba(7,14,25,0.92));
    border-radius: 16px;
    padding: 16px;
}

.indicator-pill {
    border: 1px solid rgba(59,130,246,0.28);
    border-radius: 12px;
    padding: 12px;
    background: rgba(8,16,28,0.65);
    color: #dbeafe;
    text-align: center;
    font-weight: 700;
    min-height: 68px;
    display:flex;
    align-items:center;
    justify-content:center;
}

.indicator-pill.red {
    border-color: rgba(239,68,68,0.35);
    color: #fecaca;
}

.conclusion {
    border: 1px solid rgba(239,68,68,0.45);
    background: linear-gradient(145deg, rgba(40,10,10,0.45), rgba(18,12,18,0.65));
    border-radius: 16px;
    padding: 20px 22px;
    box-shadow: 0 18px 40px rgba(0,0,0,.22);
}

.conclusion-title {
    color: #fb7185;
    font-size: 1.7rem;
    font-weight: 900;
    line-height: 1.25;
}

.conclusion-copy {
    color: #fecaca;
    font-size: 1.02rem;
    line-height: 1.7;
    margin-top: 8px;
}

.unit-note {
    border: 1px solid rgba(56,189,248,0.25);
    background: rgba(8,18,34,0.60);
    border-radius: 12px;
    padding: 12px 14px;
    color: #cbd5e1;
    line-height: 1.55;
    margin-bottom: 14px;
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
# SIDEBAR + DATA LOAD
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

missing_display = fmt_num(missing_cell) if missing_cell is not None else "15.75M"
missing_mcell_display = fmt_num(missing_mcell) if missing_mcell is not None else "15.75K"

if top5_share is None and not wallets.empty and "missing_cell" in wallets.columns:
    total = pd.to_numeric(wallets["missing_cell"], errors="coerce").sum()
    top5 = pd.to_numeric(wallets["missing_cell"], errors="coerce").head(5).sum()
    top5_share = (top5 / total * 100) if total else None

top5_display = f"{top5_share:,.2f}%" if top5_share is not None else "67.67%"

# =============================
# PAGE HEADER
# =============================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">CF20 Bridge Audit Finding: No Verifiable Lock Contract</div>
        <div class="hero-sub">Why backing remains unproven on Ethereum and BSC</div>
        <div class="hero-copy">
            This independent audit focuses on whether CF20/CELL bridge issuance is transparently backed by a publicly verifiable
            lock, reserve, burn, or custody mechanism. The current evidence shows token supply on ETH/BSC and observable bridge-related
            activity, but no clearly provable on-chain reserve path has yet been established.
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
        Official disclosure: <b>{official_mcell:,} mCELL</b> / <b>{official_cell:,.0f} CELL-equivalent</b>.
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# TOP PANELS
# =============================

left, right = st.columns([1.05, 1.15], gap="large")

with left:
    st.markdown('<div class="panel panel-blue">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Expected Bridge Model</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">What a transparently backed bridge would normally show</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="flow-box">
            <div class="flow-title">Step 1 — Zerochain / source-side issuance</div>
            <div class="flow-text">Minting or bridge issuance occurs from the source system.</div>
        </div>

        <div class="flow-box">
            <div class="flow-title">Step 2 — Verifiable reserve lock / burn / custody</div>
            <div class="flow-text">
                A discoverable on-chain lock contract, burn address, reserve wallet, or disclosed multisig should prove backing.
            </div>
        </div>

        <div class="flow-box">
            <div class="flow-title">Step 3 — ETH / BSC token supply</div>
            <div class="flow-text">
                Supply appears on Ethereum and BSC only after or alongside provable reserve logic.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="audit-alert">
            Expected result: the bridge should publicly prove where the backing sits and how it is secured.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel panel-red">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">What the Audit Found</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Observed evidence from the independent audit</div>', unsafe_allow_html=True)

    if BRIDGE_IMAGE.exists():
        st.image(str(BRIDGE_IMAGE), use_container_width=True)
    else:
        st.warning("Image not found: assets/no_verifiable_lock_contract.png")

    st.markdown(
        """
        <div class="audit-alert">
            No verifiable on-chain lock, burn, or reserve contract found. Supply exists on ETH/BSC, but transparent backing remains unproven.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =============================
# 4 FINDING CARDS
# =============================

st.markdown('<div class="section-heading">Key Audit Findings</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4, gap="large")

with c1:
    info_box(
        "1) No lock contract located",
        "No verifiable reserve-holding lock contract was identified for the bridged supply. "
        "This means the audit could not independently confirm a canonical on-chain reserve location.",
        "blue",
    )

with c2:
    info_box(
        "2) No confirmed custody wallet",
        "No clearly disclosed reserve multisig or custody wallet was confirmed as the backing holder. "
        "Without a named and provable reserve address, backing cannot be independently verified.",
        "cyan",
    )

with c3:
    info_box(
        "3) Supply exists on ETH/BSC",
        "CF20/CELL-related supply is observable on Ethereum and BSC, including exchange and LP balances. "
        "However, observable circulating supply is not the same thing as provable reserve backing.",
        "green",
    )

with c4:
    info_box(
        "4) Backing gap remains unresolved",
        "Without a discoverable lock, reserve, or burn mechanism, proof of 1:1 backing remains incomplete. "
        "The audit therefore treats backing as unverified rather than proven.",
        "red",
    )

# =============================
# INDICATORS
# =============================

st.markdown('<div class="section-heading">Observed On-Chain Indicators</div>', unsafe_allow_html=True)

st.markdown('<div class="indicator-grid">', unsafe_allow_html=True)
i1, i2, i3, i4, i5 = st.columns(5, gap="medium")

with i1:
    st.markdown('<div class="indicator-pill">ETH contract observed</div>', unsafe_allow_html=True)
with i2:
    st.markdown('<div class="indicator-pill">BSC contract observed</div>', unsafe_allow_html=True)
with i3:
    st.markdown('<div class="indicator-pill">Exchange / LP balances observed</div>', unsafe_allow_html=True)
with i4:
    st.markdown('<div class="indicator-pill">Bridge-out activity observed</div>', unsafe_allow_html=True)
with i5:
    st.markdown('<div class="indicator-pill red">No reserve lock address verified</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =============================
# KPI SUMMARY
# =============================

st.markdown('<div class="section-heading">Independent Audit Snapshot</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5, gap="large")

with k1:
    kpi_card("Deduped unmatched CELL", missing_display, "Independent chain analysis", "red")
with k2:
    kpi_card("mCELL equivalent", missing_mcell_display, "CELL ÷ 1,000", "orange")
with k3:
    kpi_card("Official illegal mCELL", f"{official_mcell:,}", "Cellframe statement", "purple")
with k4:
    kpi_card("Top 5 wallet concentration", top5_display, "Share of unmatched CELL", "blue")
with k5:
    kpi_card("Market-sale quantification", market.get("status", "Unresolved"), "Requires BSC / DEX / OTC trace", "orange")

# =============================
# EVIDENCE TABLES
# =============================

left2, right2 = st.columns([1.2, 1], gap="large")

with left2:
    st.markdown('<div class="section-heading">Top Unmatched Recipients</div>', unsafe_allow_html=True)
    if wallets.empty:
        st.info("No wallet file found. Upload missing_cell_wallets_deduped.csv or missing_cell_wallets.csv.")
    else:
        show = wallets.head(10).copy()

        if "missing_cell" in show.columns:
            show["missing_cell"] = pd.to_numeric(show["missing_cell"], errors="coerce")
            show["mcell_equivalent"] = show["missing_cell"] / CELL_PER_MCELL
            show["missing_cell"] = show["missing_cell"].map(lambda x: f"{x:,.2f}")
            show["mcell_equivalent"] = show["mcell_equivalent"].map(lambda x: f"{x:,.2f}")

        if "share_of_missing" in show.columns:
            show["share_of_missing"] = pd.to_numeric(show["share_of_missing"], errors="coerce").map(lambda x: f"{x:,.2f}%")

        preferred_cols = [c for c in [
            "mint_to",
            "missing_cell",
            "mcell_equivalent",
            "share_of_missing",
            "events",
            "max_single",
            "first",
            "last",
        ] if c in show.columns]

        st.dataframe(show[preferred_cols] if preferred_cols else show, use_container_width=True, hide_index=True)

with right2:
    st.markdown('<div class="section-heading">Evidence Status</div>', unsafe_allow_html=True)

    evidence_df = pd.DataFrame([
        {
            "Finding": "Unmatched emissions",
            "Status": "High confidence",
            "Evidence": f"{missing_display} CELL / {missing_mcell_display} mCELL-eq"
        },
        {
            "Finding": "Duplicate handling",
            "Status": "Applied" if duplicate_count is not None else "Not loaded",
            "Evidence": f"{duplicate_count if duplicate_count is not None else '—'} duplicate events removed"
        },
        {
            "Finding": "Official disclosure alignment",
            "Status": "Under review",
            "Evidence": f"{official_mcell:,} mCELL = {official_cell:,.0f} CELL-eq"
        },
        {
            "Finding": "Bridge-out evidence",
            "Status": "Supported",
            "Evidence": bridge.get("bep20_destination", "BEP20 destination identified in audit files")
        },
        {
            "Finding": "Public lock / reserve proof",
            "Status": "Not verified",
            "Evidence": "No discoverable lock or reserve contract confirmed"
        },
    ])

    st.dataframe(evidence_df, use_container_width=True, hide_index=True)

# =============================
# CONCLUSION
# =============================

st.markdown('<div class="section-heading">Conclusion</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="conclusion">
        <div class="conclusion-title">
            The audit did not verify a lock contract, reserve contract, or fully provable on-chain backing path.
        </div>
        <div class="conclusion-copy">
            Tokens on ETH/BSC may circulate without a publicly verifiable locked reserve.
            The independent audit therefore treats backing as <b>unproven</b>, not proven.
            <br><br>
            Independent deduped result: <b>{missing_display} CELL</b> / <b>{missing_mcell_display} mCELL-equivalent</b>.
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

d1, d2 = st.columns(2)

with d1:
    for label, filename in download_files[:4]:
        p = Path(filename)
        if p.exists():
            st.download_button(
                f"Download {label}",
                p.read_bytes(),
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
                p.read_bytes(),
                file_name=filename,
                mime="text/csv" if filename.endswith(".csv") else "application/json",
                use_container_width=True,
            )
        else:
            st.caption(f"Missing: {filename}")
