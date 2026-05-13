import json
from pathlib import Path
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st


# ==============================
# CONFIG
# ==============================

st.set_page_config(
    page_title="CELL / CF20 On-Chain Audit",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(".")


# ==============================
# HELPERS
# ==============================

def load_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        return default
    return default


def load_csv(path: Path):
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()


def dec(value, default="0"):
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def compact(value):
    d = dec(value)
    sign = "-" if d < 0 else ""
    d = abs(d)
    if d >= Decimal("1000000000"):
        return f"{sign}{d / Decimal('1000000000'):.2f}B"
    if d >= Decimal("1000000"):
        return f"{sign}{d / Decimal('1000000'):.2f}M"
    if d >= Decimal("1000"):
        return f"{sign}{d / Decimal('1000'):.2f}K"
    return f"{sign}{d:.2f}"


def fmt(value, places=2):
    d = dec(value)
    return f"{d:,.{places}f}"


def anchor(name: str):
    st.markdown(f'<a id="{name}"></a>', unsafe_allow_html=True)


def show_df(df: pd.DataFrame, height=None):
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True, height=height)


def file_present(path: str):
    p = ROOT / path
    return p.exists()


# ==============================
# LOAD DATA
# ==============================

reserve = load_json(ROOT / "reserve_backing_reconciliation.json")
reserve_totals = reserve.get("totals", {}) if isinstance(reserve, dict) else {}

trace_c3b8 = load_json(ROOT / "auto_trace_c3b8_summary.json")
trace_c3b8_recipients = load_csv(ROOT / "auto_trace_c3b8_recipient_summary.csv")

trace_65def = load_json(ROOT / "auto_trace_65def_summary.json")
trace_da8a = load_json(ROOT / "auto_trace_da8a_summary.json")

trace_8bbf = load_json(ROOT / "auto_trace_8bbf_combined_summary.json")
trace_8bbf_recipients = load_csv(ROOT / "auto_trace_8bbf_combined_recipient_summary.csv")

trace_35ce = load_json(ROOT / "auto_trace_35ce_summary.json")
trace_35ce_recipients = load_csv(ROOT / "auto_trace_35ce_recipient_summary.csv")

trace_a2c1 = load_json(ROOT / "auto_trace_a2c1_combined_summary.json")

oldcell_c3b8 = load_json(ROOT / "auto_trace_oldcell_c3b8_summary.json")
oldcell_8929 = load_json(ROOT / "auto_trace_oldcell_8929_summary.json")
oldcell_child_summary = load_csv(ROOT / "oldcell_458b_child_probe_summary.csv")
oldcell_secondary_summary = load_csv(ROOT / "oldcell_secondary_child_probe_summary.csv")

mexc_label_report = load_csv(ROOT / "mexc_label_check_report.csv")
mexc_pattern_report = load_csv(ROOT / "mexc_deposit_pattern_check_report.csv")


# ==============================
# CURRENT VERIFIED VALUES
# ==============================

GATEIO_ROUTE_TOTAL = Decimal("2596567.55466338")
BSC_TOTAL_SUPPLY = dec(
    reserve_totals.get("bsc_total_supply_cell")
    or reserve.get("bsc_total_supply_cell")
    or "33300000"
)
ETH_BACKING_CANDIDATES = dec(
    reserve_totals.get("eth_backing_candidate_included_cell")
    or reserve.get("eth_backing_candidate_included_cell")
    or "990044.19498039"
)
BACKING_GAP = dec(
    reserve_totals.get("bsc_supply_minus_eth_backing_candidate_cell")
    or reserve.get("bsc_supply_minus_eth_backing_candidate_cell")
    or "32309955.80501961"
)

OLD_CELL_BRIDGE_UNLOCK = Decimal("5207505.2")
OLD_CELL_A9AD_HELD = Decimal("2625551.2")

PUBLIC_MEXC_HITS = 0
if not mexc_label_report.empty and "status" in mexc_label_report.columns:
    PUBLIC_MEXC_HITS += int(
        mexc_label_report["status"]
        .isin(["known_mexc_label", "bscscan_page_contains_mexc_keyword"])
        .sum()
    )
if not mexc_pattern_report.empty and "status" in mexc_pattern_report.columns:
    PUBLIC_MEXC_HITS += int(
        (mexc_pattern_report["status"] == "known_mexc_route_detected").sum()
    )


# ==============================
# CSS
# ==============================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

:root {
  --bg:#020617;
  --panel:#07111f;
  --panel2:#0b1627;
  --text:#f8fafc;
  --muted:#94a3b8;
  --line:rgba(148,163,184,.18);
  --blue:#38bdf8;
  --green:#34d399;
  --orange:#fb923c;
  --red:#fb7185;
  --purple:#a78bfa;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
}

.stApp {
  background:
    radial-gradient(circle at 20% 0%, rgba(56,189,248,.18), transparent 26%),
    radial-gradient(circle at 80% 10%, rgba(167,139,250,.13), transparent 32%),
    linear-gradient(180deg, #020617 0%, #030712 58%, #020617 100%);
  color: var(--text);
}

.block-container {
  max-width: 1280px;
  padding-top: 2rem;
  padding-bottom: 5rem;
}

a { color: inherit; text-decoration:none; }

.topbar {
  position: sticky;
  top: 0;
  z-index: 999;
  backdrop-filter: blur(18px);
  background: rgba(2,6,23,.76);
  border:1px solid var(--line);
  border-radius: 999px;
  padding: 10px 14px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 14px;
  margin-bottom: 22px;
  box-shadow: 0 18px 60px rgba(0,0,0,.32);
}

.brand {
  display:flex;
  align-items:center;
  gap:10px;
  font-weight:900;
  letter-spacing:-.04em;
}

.brand-dot {
  width:12px;
  height:12px;
  border-radius:50%;
  background:linear-gradient(135deg,var(--blue),var(--green));
  box-shadow:0 0 26px rgba(56,189,248,.85);
}

.nav {
  display:flex;
  align-items:center;
  gap: 6px;
  flex-wrap:wrap;
  justify-content:flex-end;
}

.nav a {
  font-size:.80rem;
  font-weight:800;
  color:#cbd5e1;
  padding:8px 10px;
  border-radius:999px;
}

.nav a:hover {
  color:white;
  background:rgba(56,189,248,.12);
}

.nav .cta {
  background:linear-gradient(135deg, rgba(56,189,248,.22), rgba(52,211,153,.16));
  border:1px solid rgba(56,189,248,.30);
}

.hero {
  border:1px solid var(--line);
  border-radius: 32px;
  padding: 38px;
  overflow:hidden;
  position:relative;
  background:
    linear-gradient(135deg, rgba(8,20,36,.92), rgba(2,6,23,.80)),
    radial-gradient(circle at 75% 25%, rgba(56,189,248,.25), transparent 32%);
  box-shadow:0 24px 80px rgba(0,0,0,.38);
}

.eyebrow {
  display:inline-flex;
  gap:8px;
  align-items:center;
  padding:7px 11px;
  border-radius:999px;
  border:1px solid rgba(56,189,248,.28);
  color:#bae6fd;
  background:rgba(56,189,248,.08);
  font-size:.78rem;
  font-weight:900;
  text-transform:uppercase;
  letter-spacing:.08em;
}

.hero h1 {
  margin:.85rem 0 .9rem;
  font-size: clamp(2.4rem, 6vw, 5.2rem);
  line-height:.92;
  letter-spacing:-.08em;
  max-width: 980px;
}

.hero p {
  color:#cbd5e1;
  font-size:1.08rem;
  line-height:1.75;
  max-width: 930px;
}

.hero-actions {
  display:flex;
  gap:12px;
  flex-wrap:wrap;
  margin-top: 22px;
}

.btn {
  padding:11px 15px;
  border-radius:999px;
  border:1px solid var(--line);
  color:#e2e8f0;
  font-weight:900;
  font-size:.86rem;
  background:rgba(15,23,42,.72);
}

.btn-primary {
  background:linear-gradient(135deg, rgba(56,189,248,.28), rgba(52,211,153,.18));
  border-color:rgba(56,189,248,.38);
}

.grid {
  display:grid;
  gap:14px;
}

.metrics-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 18px 0 26px;
}

.metric-card, .section, .claim-card {
  border:1px solid var(--line);
  background:linear-gradient(145deg, rgba(8,20,36,.88), rgba(2,6,23,.72));
  border-radius: 24px;
  box-shadow:0 18px 60px rgba(0,0,0,.24);
}

.metric-card {
  padding:18px;
  min-height: 145px;
}

.metric-label {
  color:#94a3b8;
  font-size:.78rem;
  font-weight:900;
  text-transform:uppercase;
  letter-spacing:.08em;
}

.metric-value {
  color:#f8fafc;
  font-weight:950;
  font-size: clamp(1.6rem, 3vw, 2.5rem);
  letter-spacing:-.06em;
  margin: 10px 0 8px;
}

.metric-sub {
  color:#94a3b8;
  font-size:.83rem;
  line-height:1.45;
}

.tone-blue { border-color:rgba(56,189,248,.24); }
.tone-green { border-color:rgba(52,211,153,.24); }
.tone-orange { border-color:rgba(251,146,60,.28); }
.tone-red { border-color:rgba(251,113,133,.30); }
.tone-purple { border-color:rgba(167,139,250,.28); }

.section {
  padding: 26px;
  margin: 22px 0;
}

.section-title {
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:20px;
  margin-bottom: 16px;
}

.section h2 {
  font-size: clamp(1.55rem, 3vw, 2.35rem);
  letter-spacing:-.06em;
  margin:0 0 6px;
}

.section p {
  color:#94a3b8;
  line-height:1.65;
  margin:0;
}

.pill {
  display:inline-flex;
  align-items:center;
  white-space:nowrap;
  border-radius:999px;
  padding:7px 10px;
  font-size:.76rem;
  font-weight:950;
  border:1px solid var(--line);
}

.pill-blue { color:#bae6fd; background:rgba(56,189,248,.10); border-color:rgba(56,189,248,.30); }
.pill-green { color:#bbf7d0; background:rgba(52,211,153,.10); border-color:rgba(52,211,153,.28); }
.pill-orange { color:#fed7aa; background:rgba(251,146,60,.10); border-color:rgba(251,146,60,.30); }
.pill-red { color:#fecdd3; background:rgba(251,113,133,.10); border-color:rgba(251,113,133,.32); }
.pill-purple { color:#ddd6fe; background:rgba(167,139,250,.10); border-color:rgba(167,139,250,.30); }

.quick-grid {
  display:grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap:12px;
}

.quick-card {
  border:1px solid rgba(148,163,184,.16);
  border-radius:18px;
  padding:15px;
  min-height:98px;
  background:rgba(15,23,42,.46);
  display:flex;
  flex-direction:column;
  gap:7px;
}

.quick-card:hover {
  border-color:rgba(56,189,248,.52);
  background:rgba(56,189,248,.08);
  transform:translateY(-1px);
}

.quick-card b {
  color:#f8fafc;
  letter-spacing:-.03em;
}

.quick-card span {
  color:#94a3b8;
  font-size:.82rem;
  line-height:1.45;
}

.note, .success-note, .warning-note {
  border-radius:18px;
  padding:16px 18px;
  line-height:1.6;
  color:#cbd5e1;
  border:1px solid var(--line);
  background:rgba(15,23,42,.48);
}

.success-note {
  border-color:rgba(52,211,153,.28);
  background:rgba(52,211,153,.08);
}

.warning-note {
  border-color:rgba(251,146,60,.30);
  background:rgba(251,146,60,.08);
}

.claim-grid {
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap:14px;
}

.claim-card {
  padding:20px;
}

.claim-card h3 {
  margin:0 0 8px;
  letter-spacing:-.04em;
}

.claim-card p {
  color:#94a3b8;
  line-height:1.55;
}

[data-testid="stDataFrame"] {
  border:1px solid rgba(148,163,184,.16);
  border-radius:16px;
  overflow:hidden;
}

@media(max-width: 1100px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .quick-grid { grid-template-columns: repeat(2, 1fr); }
  .claim-grid { grid-template-columns: 1fr; }
}

@media(max-width: 720px) {
  .topbar { border-radius:24px; align-items:flex-start; flex-direction:column; }
  .nav { justify-content:flex-start; }
  .metrics-grid { grid-template-columns: 1fr; }
  .quick-grid { grid-template-columns: 1fr; }
  .hero { padding:26px; }
}
</style>
    """,
    unsafe_allow_html=True,
)


# ==============================
# NAV + HERO
# ==============================

st.markdown(
    """
<div class="topbar">
  <div class="brand"><span class="brand-dot"></span> CELL / CF20 Audit</div>
  <div class="nav">
    <a href="#overview">Overview</a>
    <a href="#trust">Trust</a>
    <a href="#supply">Supply</a>
    <a href="#traces">Traces</a>
    <a href="#oldcell">Old-CELL Claim</a>
    <a href="#reserve">Reserve</a>
    <a class="cta" href="#evidence">Evidence</a>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

anchor("overview")

st.markdown(
    """
<div class="hero">
  <div class="eyebrow">Independent on-chain audit dashboard</div>
  <h1>Supply creation, custody routing, exchange exposure, and reserve reconciliation.</h1>
  <p>
    This site summarizes verified on-chain evidence for CELL / CF20 across Ethereum and BSC.
    It separates verified facts from unresolved claims, including BSC mint routing, Gate.io-bound exposure,
    old-CELL bridge/unlock flows, and the public MEXC dumping allegation.
  </p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="#findings">View key findings</a>
    <a class="btn" href="#trust">Trust standard</a>
    <a class="btn" href="#oldcell">Old-CELL claim</a>
    <a class="btn" href="#reserve">Reserve reconciliation</a>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)


# ==============================
# TOP METRICS
# ==============================

anchor("findings")

cols = st.columns(4)
with cols[0]:
    st.markdown(
        f"""
<div class="metric-card tone-green">
  <div class="metric-label">Verified Gate.io route</div>
  <div class="metric-value">2.60M</div>
  <div class="metric-sub">2,596,567.55 CELL verified traced BSC mint-path exposure</div>
</div>
        """,
        unsafe_allow_html=True,
    )
with cols[1]:
    st.markdown(
        """
<div class="metric-card tone-blue">
  <div class="metric-label">Central BSC wallets</div>
  <div class="metric-value">2</div>
  <div class="metric-sub">0x65def and 0xc3b8 traced to zero balance</div>
</div>
        """,
        unsafe_allow_html=True,
    )
with cols[2]:
    st.markdown(
        f"""
<div class="metric-card tone-red">
  <div class="metric-label">Backing gap</div>
  <div class="metric-value">{compact(BACKING_GAP)}</div>
  <div class="metric-sub">Conservative unresolved BSC backing gap</div>
</div>
        """,
        unsafe_allow_html=True,
    )
with cols[3]:
    st.markdown(
        f"""
<div class="metric-card tone-orange">
  <div class="metric-label">Public MEXC label hits</div>
  <div class="metric-value">{PUBLIC_MEXC_HITS}</div>
  <div class="metric-sub">No publicly labelled MEXC endpoint found so far</div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ==============================
# QUICK JUMP
# ==============================

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Audit sections</h2>
      <p>Use these quick links to move through the evidence without crowding the main navigation.</p>
    </div>
    <span class="pill pill-blue">Evidence-first layout</span>
  </div>
  <div class="quick-grid">
    <a class="quick-card" href="#trust"><b>Trust Standard</b><span>How findings are classified and what public data can prove.</span></a>
    <a class="quick-card" href="#supply"><b>Verified Supply</b><span>ETH/BSC supply, mint events, and supply accounting.</span></a>
    <a class="quick-card" href="#traces"><b>Central BSC Traces</b><span>0x65def, 0xc3b8, 0xda8a, 8bbf, and 35ce traces.</span></a>
    <a class="quick-card" href="#oldcell"><b>Old-CELL Claim Check</b><span>5M+ old-CELL bridge/unlock and MEXC allegation.</span></a>
    <a class="quick-card" href="#reserve"><b>Reserve Backing</b><span>Current backing candidates and unresolved gap.</span></a>
    <a class="quick-card" href="#gateio"><b>Exchange Exposure</b><span>Verified Gate.io-bound route exposure and caveats.</span></a>
    <a class="quick-card" href="#downstream"><b>Downstream Branches</b><span>8bbf, 35ce, and a2c1 distribution behavior.</span></a>
    <a class="quick-card" href="#evidence"><b>Evidence Files</b><span>CSV/JSON outputs and downloadable audit artifacts.</span></a>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)


# ==============================
# TRUST SECTION
# ==============================

anchor("trust")

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Trust, Limits, and Verification Standard</h2>
      <p>This audit is designed to separate what public on-chain evidence proves from what remains unresolved or requires off-chain records.</p>
    </div>
    <span class="pill pill-green">Evidence standard</span>
  </div>

  <div class="claim-grid">
    <div class="claim-card">
      <h3>What this audit proves</h3>
      <p>Contract-level supply, mint events, token movements, traced wallet balances, and routes into publicly labelled exchange custody where labels are available.</p>
    </div>
    <div class="claim-card">
      <h3>What this audit does not overclaim</h3>
      <p>Exact CEX sale proceeds, exchange-internal trading, final beneficiaries, or private exchange-account activity without supporting records.</p>
    </div>
    <div class="claim-card">
      <h3>How findings are classified</h3>
      <p>Findings are treated as verified, supported, unresolved, or unverified depending on transaction-level evidence, traces, and public labels.</p>
    </div>
    <div class="claim-card">
      <h3>How to independently verify</h3>
      <p>Each major finding is backed by CSV/JSON trace outputs and transaction hashes. Anyone can replay the RPC scans or inspect the evidence files.</p>
    </div>
  </div>

  <br>

  <div class="success-note">
    <b>Verification principle:</b> A wallet path is only called “verified” when token movement is supported by on-chain events.
    A CEX route is called “exchange exposure” unless there is separate evidence of actual exchange-side sale execution.
  </div>

  <br>

  <div class="warning-note">
    <b>Limitations:</b> Public blockchain data cannot see inside centralized exchanges. A deposit to Gate.io, MEXC, Binance, or another CEX can prove exchange-custody routing,
    but not sale price, internal trade, account owner, or withdrawal beneficiary without exchange records.
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

trust_rows = pd.DataFrame([
    {
        "Evidence type": "Token mint / burn / transfer event",
        "Can prove": "Token creation, movement, amount, sender, recipient, block, transaction hash",
        "Cannot prove alone": "Human intent, off-chain agreements, or final exchange outcome",
    },
    {
        "Evidence type": "Wallet balance trace",
        "Can prove": "Whether a wallet held, distributed, or reached zero balance over a block range",
        "Cannot prove alone": "Who legally controlled the wallet unless attribution evidence exists",
    },
    {
        "Evidence type": "Public exchange label",
        "Can prove": "Route exposure to a labelled exchange custody endpoint",
        "Cannot prove alone": "Whether the tokens were sold inside the exchange",
    },
    {
        "Evidence type": "Unlabelled wallet",
        "Can prove": "On-chain routing behavior",
        "Cannot prove alone": "Whether the wallet is a private CEX deposit wallet",
    },
    {
        "Evidence type": "Reserve/backing candidate",
        "Can prove": "Current observed balance of identified candidate wallets",
        "Cannot prove alone": "Full backing unless all reserve/custody wallets are disclosed and verified",
    },
])
st.markdown("### Evidence Standard Matrix")
show_df(trust_rows)

confidence_rows = pd.DataFrame([
    {
        "Label": "Verified",
        "Meaning": "Direct on-chain evidence supports the finding.",
        "Example": "BSC mint event; 0xc3b8 traced to zero; Gate.io-labelled route exposure.",
    },
    {
        "Label": "Supported",
        "Meaning": "Evidence strongly supports the claim, but one step may rely on public labels or context.",
        "Example": "A route into a labelled exchange custody wallet.",
    },
    {
        "Label": "Unresolved",
        "Meaning": "Evidence is incomplete or further wallet/custody disclosure is required.",
        "Example": "Full reserve/backing reconciliation.",
    },
    {
        "Label": "Unverified",
        "Meaning": "The claim has not been proven by current public on-chain evidence.",
        "Example": "Old-CELL dumping on MEXC.",
    },
])
st.markdown("### Finding Confidence Labels")
show_df(confidence_rows)


# ==============================
# CLAIMS VS EVIDENCE
# ==============================

anchor("claims")

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Claims vs evidence</h2>
      <p>The audit avoids overclaiming. Each major finding is classified by what the public chain data can actually prove.</p>
    </div>
    <span class="pill pill-green">Audit-safe</span>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

claim_rows = pd.DataFrame([
    {
        "Finding": "ETH/BSC supply creation",
        "Status": "Verified",
        "Evidence": "ETH totalSupply 30.3M and BSC totalSupply 33.3M observed; BSC mint event identified.",
    },
    {
        "Finding": "Central BSC supply wallets traced",
        "Status": "Verified",
        "Evidence": "0x65def and 0xc3b8 traced to zero; downstream branches identified.",
    },
    {
        "Finding": "Gate.io-bound route exposure",
        "Status": "Verified route exposure",
        "Evidence": "At least 2,596,567.55 CELL from traced BSC supply paths routed to Gate.io-labelled custody.",
    },
    {
        "Finding": "Exact realized sale proceeds",
        "Status": "Unresolved",
        "Evidence": "CEX-internal trading is off-chain and requires exchange/account records.",
    },
    {
        "Finding": "Reserve/backing reconciliation",
        "Status": "Partial / unresolved",
        "Evidence": "Conservative verified ETH backing candidates do not reconcile BSC totalSupply; current gap ~32.31M CELL.",
    },
    {
        "Finding": "Old-CELL MEXC dumping claim",
        "Status": "Unverified",
        "Evidence": "Bridge/unlock is supported; zero publicly labelled MEXC endpoints found in traced addresses so far.",
    },
])
show_df(claim_rows)


# ==============================
# SUPPLY
# ==============================

anchor("supply")

st.markdown(
    f"""
<div class="section">
  <div class="section-title">
    <div>
      <h2>Verified supply and mint path</h2>
      <p>Contract-level supply and mint events are the foundation of the audit. BSC supply was minted in a single 33.3M CELL event to the original mint recipient.</p>
    </div>
    <span class="pill pill-green">Supply verified</span>
  </div>

  <div class="grid metrics-grid">
    <div class="metric-card tone-blue">
      <div class="metric-label">ETH totalSupply</div>
      <div class="metric-value">30.30M</div>
      <div class="metric-sub">Ethereum CELL contract supply</div>
    </div>
    <div class="metric-card tone-purple">
      <div class="metric-label">BSC totalSupply</div>
      <div class="metric-value">33.30M</div>
      <div class="metric-sub">BSC CELL v2 contract supply</div>
    </div>
    <div class="metric-card tone-green">
      <div class="metric-label">BSC mint event</div>
      <div class="metric-value">33.30M</div>
      <div class="metric-sub">Minted to 0x65def...</div>
    </div>
    <div class="metric-card tone-orange">
      <div class="metric-label">Raw ETH+BSC supply</div>
      <div class="metric-value">63.60M</div>
      <div class="metric-sub">Contract-level supply across indexed chains</div>
    </div>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

supply_path_rows = pd.DataFrame([
    {
        "Step": "BSC mint",
        "Amount": "33,300,000 CELL",
        "From": "0x0000...0000",
        "To": "0x65def...68f27",
        "Status": "Verified",
    },
    {
        "Step": "Primary custody transfer",
        "Amount": "30,000,000 CELL",
        "From": "0x65def...68f27",
        "To": "0xc3b8...0ab8",
        "Status": "Verified",
    },
    {
        "Step": "Central wallet traces",
        "Amount": "0 final balances",
        "From": "0x65def / 0xc3b8",
        "To": "Downstream wallets",
        "Status": "Traced to zero",
    },
])
show_df(supply_path_rows)


# ==============================
# CENTRAL TRACES
# ==============================

anchor("traces")

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Central BSC supply wallet traces</h2>
      <p>The two core BSC supply wallets have been traced to zero balance. This establishes the main custody and distribution routes from the BSC mint.</p>
    </div>
    <span class="pill pill-green">Central traces complete</span>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

central_rows = pd.DataFrame([
    {
        "Wallet": "0x65def3ea531fd80354ec11c611Ae4fAa06068F27",
        "Role": "Original BSC mint recipient",
        "Trace status": "Traced to zero",
        "Key result": "39.31M outbound; includes 30M to 0xc3b8, 2.635M to 0xda8a, 656,567.55 to Gate.io.",
    },
    {
        "Wallet": "0xc3b8a652e59d59a71b00808c1fb2432857080ab8",
        "Role": "Primary BSC custody wallet",
        "Trace status": "Traced to zero",
        "Key result": "31.10M outbound across 19 recipients; includes 6.4M back to 0x65def and 1M to 0xda8a.",
    },
    {
        "Wallet": "0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5",
        "Role": "Consolidation / cross-cluster wallet",
        "Trace status": "Traced to zero in captured route",
        "Key result": "940,000 CELL routed to Gate.io-labelled endpoint.",
    },
])
show_df(central_rows)


# ==============================
# GATE.IO
# ==============================

anchor("gateio")

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Verified exchange route exposure</h2>
      <p>Gate.io-bound route exposure is verified, but CEX-internal sale execution remains off-chain.</p>
    </div>
    <span class="pill pill-green">Route exposure verified</span>
  </div>

  <div class="grid metrics-grid">
    <div class="metric-card tone-green">
      <div class="metric-label">Verified Gate.io-bound route</div>
      <div class="metric-value">2.60M</div>
      <div class="metric-sub">2,596,567.55 CELL from traced BSC supply paths</div>
    </div>
    <div class="metric-card tone-orange">
      <div class="metric-label">Exact sale proceeds</div>
      <div class="metric-value">Unknown</div>
      <div class="metric-sub">CEX internal trading is not visible on-chain</div>
    </div>
    <div class="metric-card tone-blue">
      <div class="metric-label">Endpoint</div>
      <div class="metric-value">Gate.io</div>
      <div class="metric-sub">0x0d070... Gate.io-labelled custody endpoint</div>
    </div>
    <div class="metric-card tone-purple">
      <div class="metric-label">Evidence level</div>
      <div class="metric-value">Route</div>
      <div class="metric-sub">Proves exchange custody routing, not final trade outcome</div>
    </div>
  </div>

  <div class="warning-note">
    <b>Important caveat:</b> Verified CEX route exposure is not the same as realized sale proceeds.
    Public chain data proves tokens reached Gate.io-labelled custody, but any exchange-internal trading, sale price,
    proceeds, or final beneficiary requires exchange/account records.
  </div>
</div>
    """,
    unsafe_allow_html=True,
)


# ==============================
# DOWNSTREAM
# ==============================

anchor("downstream")

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Downstream distribution traces</h2>
      <p>Large downstream branches were traced to determine whether they behaved like reserve wallets or distribution / pass-through wallets.</p>
    </div>
    <span class="pill pill-blue">Branch analysis</span>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

downstream_rows = pd.DataFrame([
    {
        "Wallet": "0x8bbf051e8dfaa9c477bbd63fa5013ab3b988e218",
        "Trace status": "Traced to zero",
        "Interpretation": "High-volume downstream distribution wallet, not reserve-like.",
        "Key output": "Largest output 552,542.49 CELL to 0x35ce...",
    },
    {
        "Wallet": "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60",
        "Trace status": "Traced to zero",
        "Interpretation": "Bridge/aggregator-style pass-through distribution node, not reserve endpoint in BSC trace.",
        "Key output": "552,542.49 CELL to 0xa2c1 and 103,911 CELL to 0xda8a.",
    },
    {
        "Wallet": "0xa2c1e0237bf4b58bc9808a579715df57522f41b2",
        "Trace status": "Partial high-activity branch",
        "Interpretation": "High-turnover downstream distribution / aggregation behavior; not reserve-like.",
        "Key output": "Partial trace across multiple parts; branch remained active.",
    },
])
show_df(downstream_rows)

if not trace_8bbf_recipients.empty:
    st.markdown("#### Top recipients from completed 8bbf trace")
    df = trace_8bbf_recipients.copy()
    if "amount_cell" in df.columns:
        df["amount_cell_num"] = pd.to_numeric(df["amount_cell"], errors="coerce")
        df = df.sort_values("amount_cell_num", ascending=False).head(20)
        df["amount_cell"] = df["amount_cell_num"].map(lambda x: f"{x:,.8f}")
        df = df.drop(columns=["amount_cell_num"], errors="ignore")
    show_df(df, height=420)


# ==============================
# OLD-CELL CLAIM
# ==============================

anchor("oldcell")

st.markdown(
    f"""
<div class="section">
  <div class="section-title">
    <div>
      <h2>Old-CELL Bridge Claim Check</h2>
      <p>A public claim alleged that 5M+ old CELL was bridged back and dumped on MEXC. The audit separates the supported bridge/unlock evidence from the unproven MEXC claim.</p>
    </div>
    <span class="pill pill-orange">Claim reviewed</span>
  </div>

  <div class="grid metrics-grid">
    <div class="metric-card tone-green">
      <div class="metric-label">Bridge/unlock into 0xc3b8</div>
      <div class="metric-value">5.21M</div>
      <div class="metric-sub">5,207,505.2 old CELL supported by tx and trace</div>
    </div>
    <div class="metric-card tone-blue">
      <div class="metric-label">0xc3b8 old-CELL final balance</div>
      <div class="metric-value">0</div>
      <div class="metric-sub">Old-CELL balance routed onward</div>
    </div>
    <div class="metric-card tone-purple">
      <div class="metric-label">Largest held branch</div>
      <div class="metric-value">2.63M</div>
      <div class="metric-sub">0xa9ad held 2,625,551.2 old CELL at scan end</div>
    </div>
    <div class="metric-card tone-red">
      <div class="metric-label">Public MEXC label hits</div>
      <div class="metric-value">{PUBLIC_MEXC_HITS}</div>
      <div class="metric-sub">No publicly labelled MEXC endpoint detected so far</div>
    </div>
  </div>

  <div class="success-note">
    <b>Supported:</b> The 5M+ old-CELL bridge/unlock into <code>0xc3b8...</code> is supported,
    and downstream routing is verified.
  </div>
  <br>
  <div class="warning-note">
    <b>Not proven:</b> The traced paths do not currently identify a publicly labelled MEXC endpoint.
    This leaves the MEXC dumping claim unverified. A private or unlabelled MEXC deposit address cannot be ruled out from public data alone.
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

oldcell_rows = pd.DataFrame([
    {
        "Route / check": "Bridge/unlock → 0xc3b8",
        "Amount": "5,207,505.2 old CELL",
        "Status": "Supported / verified",
        "Interpretation": "The 5M+ old-CELL part of the public claim is supported.",
    },
    {
        "Route / check": "0xc3b8 → 0x8929",
        "Amount": "4,487,005.2 old CELL",
        "Status": "Verified",
        "Interpretation": "Largest downstream old-CELL route.",
    },
    {
        "Route / check": "0x8929 → 0xa9ad",
        "Amount": "3,551,757.2 old CELL",
        "Status": "Partially resolved",
        "Interpretation": "0xa9ad retained 2,625,551.2 old CELL through scan end.",
    },
    {
        "Route / check": "0x8929 → 0x458b → ten 100k wallets",
        "Amount": "1,000,000 old CELL",
        "Status": "Verified split",
        "Interpretation": "Some child wallets held; moved branches routed to other wallets or back to 0xe0ca.",
    },
    {
        "Route / check": "MEXC label check",
        "Amount": "19 traced addresses checked",
        "Status": "No public MEXC hit",
        "Interpretation": "No publicly labelled MEXC endpoint detected in checked addresses.",
    },
])
show_df(oldcell_rows)

if not oldcell_child_summary.empty:
    st.markdown("#### Ten 100k old-CELL child wallets")
    show_df(oldcell_child_summary)

if not oldcell_secondary_summary.empty:
    st.markdown("#### Secondary child-wallet probe")
    show_df(oldcell_secondary_summary)

if not mexc_label_report.empty and {"address", "status", "bscscan_title"}.issubset(mexc_label_report.columns):
    st.markdown("#### MEXC public-label check")
    show_df(mexc_label_report[["address", "status", "bscscan_title"]].head(30))

if not mexc_pattern_report.empty:
    st.markdown("#### MEXC deposit-pattern check")
    cols_to_show = [c for c in [
        "address",
        "status",
        "oldcell_out_total",
        "oldcell_out_txs",
        "unique_oldcell_recipients",
        "exchange_deposit_like_heuristic",
    ] if c in mexc_pattern_report.columns]
    if cols_to_show:
        show_df(mexc_pattern_report[cols_to_show].head(40))


# ==============================
# RESERVE BACKING
# ==============================

anchor("reserve")

st.markdown(
    f"""
<div class="section">
  <div class="section-title">
    <div>
      <h2>Reserve / Backing Reconciliation</h2>
      <p>Current conservative reserve/backing candidates do not reconcile the BSC supply. Market terminals, routers, CEX, DEX, zero, and dead addresses are excluded from backing totals by default.</p>
    </div>
    <span class="pill pill-red">Partial / unresolved</span>
  </div>

  <div class="grid metrics-grid">
    <div class="metric-card tone-blue">
      <div class="metric-label">BSC totalSupply</div>
      <div class="metric-value">{compact(BSC_TOTAL_SUPPLY)}</div>
      <div class="metric-sub">BSC CELL supply requiring backing explanation</div>
    </div>
    <div class="metric-card tone-green">
      <div class="metric-label">Verified ETH backing candidates</div>
      <div class="metric-value">{compact(ETH_BACKING_CANDIDATES)}</div>
      <div class="metric-sub">{fmt(ETH_BACKING_CANDIDATES, 2)} CELL conservative backing candidates</div>
    </div>
    <div class="metric-card tone-red">
      <div class="metric-label">Open backing gap</div>
      <div class="metric-value">{compact(BACKING_GAP)}</div>
      <div class="metric-sub">{fmt(BACKING_GAP, 2)} CELL unresolved under current evidence</div>
    </div>
    <div class="metric-card tone-orange">
      <div class="metric-label">Audit status</div>
      <div class="metric-value">Open</div>
      <div class="metric-sub">Requires verified reserve wallets or bridge accounting</div>
    </div>
  </div>

  <div class="warning-note">
    <b>Audit-safe conclusion:</b> This does not prove backing does not exist. It shows that the currently identified
    and conservatively verified reserve/custody wallets do not reconcile BSC supply.
  </div>
</div>
    """,
    unsafe_allow_html=True,
)


# ==============================
# EVIDENCE FILES
# ==============================

anchor("evidence")

evidence_files = [
    "reserve_backing_reconciliation.json",
    "reserve_backing_candidates.csv",
    "reserve_backing_manual_labels.csv",
    "auto_trace_c3b8_summary.json",
    "auto_trace_c3b8_recipient_summary.csv",
    "auto_trace_65def_summary.json",
    "auto_trace_da8a_summary.json",
    "auto_trace_8bbf_combined_summary.json",
    "auto_trace_8bbf_combined_recipient_summary.csv",
    "auto_trace_35ce_summary.json",
    "auto_trace_35ce_recipient_summary.csv",
    "auto_trace_a2c1_combined_summary.json",
    "auto_trace_oldcell_c3b8_summary.json",
    "auto_trace_oldcell_8929_summary.json",
    "oldcell_458b_child_probe_summary.csv",
    "oldcell_secondary_child_probe_summary.csv",
    "mexc_label_check_report.csv",
    "mexc_deposit_pattern_check_report.csv",
]

evidence_rows = []
for f in evidence_files:
    p = ROOT / f
    evidence_rows.append({
        "File": f,
        "Present": "Yes" if p.exists() else "No",
        "Size KB": round(p.stat().st_size / 1024, 2) if p.exists() else "",
    })

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Evidence files</h2>
      <p>Generated CSV and JSON files supporting the audit findings. Missing files simply mean that trace section has not been generated in this deployment environment.</p>
    </div>
    <span class="pill pill-blue">Artifacts</span>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

show_df(pd.DataFrame(evidence_rows))


# ==============================
# FINAL STANCE
# ==============================

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Final audit stance</h2>
      <p>
        The audit verifies supply creation, core BSC custody routing, multiple completed downstream traces,
        and Gate.io-bound route exposure. It does not overclaim CEX sale proceeds or unverified MEXC dumping.
      </p>
    </div>
    <span class="pill pill-green">Current conclusion</span>
  </div>
  <div class="note">
    <b>Current headline:</b> Supply creation and BSC distribution routes are verified.
    Central BSC supply wallets and several downstream branches have been traced to zero.
    Gate.io-bound route exposure is verified for at least 2,596,567.55 CELL.
    Conservative reserve/backing reconciliation remains open with a ~32.31M CELL gap.
    The old-CELL bridge/unlock claim is supported, but the MEXC dumping claim remains unverified.
  </div>
</div>
    """,
    unsafe_allow_html=True,
)
