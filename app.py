import json
from pathlib import Path
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st


# ==============================
# CONFIG
# ==============================

st.set_page_config(
    page_title="CELL / Cellframe On-Chain Audit",
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
        if height is None:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
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
  --bg:#050b16;
  --panel:#071525;
  --panel2:#0a1f33;
  --text:#f4fbff;
  --muted:#9fb4c7;
  --line:rgba(125,211,252,.16);

  --cyan:#22d3ee;
  --blue:#38bdf8;
  --emerald:#10b981;
  --lime:#84cc16;
  --amber:#f59e0b;
  --rose:#f43f5e;
  --slate:#64748b;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
}

.stApp {
  background:
    radial-gradient(circle at 18% 0%, rgba(34,211,238,.20), transparent 26%),
    radial-gradient(circle at 90% 12%, rgba(16,185,129,.14), transparent 30%),
    radial-gradient(circle at 45% 92%, rgba(56,189,248,.08), transparent 28%),
    linear-gradient(180deg, #050b16 0%, #06111f 48%, #020617 100%);
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
  background: rgba(5,11,22,.78);
  border:1px solid rgba(34,211,238,.18);
  border-radius: 999px;
  padding: 10px 14px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 14px;
  margin-bottom: 22px;
  box-shadow: 0 18px 60px rgba(0,0,0,.34);
}

.brand {
  display:flex;
  align-items:center;
  gap:10px;
  font-weight:900;
  letter-spacing:-.04em;
  color:#ecfeff;
}

.brand-dot {
  width:12px;
  height:12px;
  border-radius:50%;
  background:linear-gradient(135deg,var(--cyan),var(--emerald));
  box-shadow:0 0 26px rgba(34,211,238,.95);
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
  color:#c7dbe8;
  padding:8px 10px;
  border-radius:999px;
}

.nav a:hover {
  color:white;
  background:rgba(34,211,238,.12);
}

.nav .cta {
  background:linear-gradient(135deg, rgba(34,211,238,.22), rgba(16,185,129,.16));
  border:1px solid rgba(34,211,238,.32);
}

.hero {
  border:1px solid rgba(34,211,238,.20);
  border-radius: 32px;
  padding: 38px;
  overflow:hidden;
  position:relative;
  background:
    linear-gradient(135deg, rgba(7,21,37,.94), rgba(5,11,22,.82)),
    radial-gradient(circle at 76% 24%, rgba(34,211,238,.22), transparent 33%),
    radial-gradient(circle at 20% 92%, rgba(16,185,129,.14), transparent 30%);
  box-shadow:0 24px 80px rgba(0,0,0,.38);
}

.eyebrow {
  display:inline-flex;
  gap:8px;
  align-items:center;
  padding:7px 11px;
  border-radius:999px;
  border:1px solid rgba(34,211,238,.30);
  color:#a5f3fc;
  background:rgba(34,211,238,.08);
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
  color:#f4fbff;
}

.hero p {
  color:#bdd2e3;
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
  border:1px solid rgba(125,211,252,.18);
  color:#e0f7ff;
  font-weight:900;
  font-size:.86rem;
  background:rgba(10,31,51,.72);
}

.btn:hover {
  border-color:rgba(34,211,238,.45);
  background:rgba(34,211,238,.10);
}

.btn-primary {
  background:linear-gradient(135deg, rgba(34,211,238,.28), rgba(16,185,129,.20));
  border-color:rgba(34,211,238,.40);
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
  border:1px solid rgba(125,211,252,.15);
  background:linear-gradient(145deg, rgba(7,21,37,.90), rgba(5,11,22,.74));
  border-radius: 24px;
  box-shadow:0 18px 60px rgba(0,0,0,.25);
}

.metric-card {
  padding:18px;
  min-height: 145px;
}

.metric-label {
  color:#9fb4c7;
  font-size:.78rem;
  font-weight:900;
  text-transform:uppercase;
  letter-spacing:.08em;
}

.metric-value {
  color:#f4fbff;
  font-weight:950;
  font-size: clamp(1.6rem, 3vw, 2.5rem);
  letter-spacing:-.06em;
  margin: 10px 0 8px;
}

.metric-sub {
  color:#9fb4c7;
  font-size:.83rem;
  line-height:1.45;
}

.tone-blue { border-color:rgba(56,189,248,.28); box-shadow:0 18px 60px rgba(56,189,248,.05); }
.tone-green { border-color:rgba(16,185,129,.30); box-shadow:0 18px 60px rgba(16,185,129,.05); }
.tone-orange { border-color:rgba(245,158,11,.30); box-shadow:0 18px 60px rgba(245,158,11,.045); }
.tone-red { border-color:rgba(244,63,94,.32); box-shadow:0 18px 60px rgba(244,63,94,.045); }
.tone-purple { border-color:rgba(34,211,238,.24); box-shadow:0 18px 60px rgba(34,211,238,.04); }

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
  color:#f4fbff;
}

.section p {
  color:#9fb4c7;
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
  border:1px solid rgba(125,211,252,.18);
}

.pill-blue { color:#a5f3fc; background:rgba(34,211,238,.10); border-color:rgba(34,211,238,.30); }
.pill-green { color:#bbf7d0; background:rgba(16,185,129,.11); border-color:rgba(16,185,129,.30); }
.pill-orange { color:#fde68a; background:rgba(245,158,11,.11); border-color:rgba(245,158,11,.32); }
.pill-red { color:#fecdd3; background:rgba(244,63,94,.11); border-color:rgba(244,63,94,.34); }
.pill-purple { color:#a5f3fc; background:rgba(34,211,238,.10); border-color:rgba(34,211,238,.30); }

.quick-grid {
  display:grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap:12px;
}

.quick-card {
  border:1px solid rgba(125,211,252,.16);
  border-radius:18px;
  padding:15px;
  min-height:98px;
  background:rgba(10,31,51,.48);
  display:flex;
  flex-direction:column;
  gap:7px;
}

.quick-card:hover {
  border-color:rgba(34,211,238,.56);
  background:rgba(34,211,238,.09);
  transform:translateY(-1px);
}

.quick-card b {
  color:#f4fbff;
  letter-spacing:-.03em;
}

.quick-card span {
  color:#9fb4c7;
  font-size:.82rem;
  line-height:1.45;
}

.note, .success-note, .warning-note {
  border-radius:18px;
  padding:16px 18px;
  line-height:1.6;
  color:#c7dbe8;
  border:1px solid rgba(125,211,252,.16);
  background:rgba(10,31,51,.50);
}

.success-note {
  border-color:rgba(16,185,129,.30);
  background:rgba(16,185,129,.09);
}

.warning-note {
  border-color:rgba(245,158,11,.32);
  background:rgba(245,158,11,.09);
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
  color:#f4fbff;
}

.claim-card p {
  color:#9fb4c7;
  line-height:1.55;
}

[data-testid="stDataFrame"] {
  border:1px solid rgba(125,211,252,.16);
  border-radius:16px;
  overflow:hidden;
}

[data-testid="stDataFrame"] * {
  font-family: 'Inter', sans-serif;
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
  <div class="brand"><span class="brand-dot"></span> CELL / Cellframe Audit</div>
  <div class="nav">
    <a href="#overview">Overview</a>
    <a href="#verdict">Verdict</a>
    <a href="#trust">Trust</a>
    <a href="#supply">Supply</a>
    <a href="#traces">Traces</a>
    <a href="#oldcell">Old-CELL Claim</a>
    <a href="#reserve">Reserve</a>
    <a href="#methodology">Methodology</a>
    <a href="#circulating">Circulating</a>
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
    This site summarizes verified on-chain evidence for CELL / Cellframe across Ethereum and BSC.
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
# EXECUTIVE VERDICT
# ==============================

anchor("verdict")

st.markdown("## Executive Verdict")
st.caption("The current audit position: what is verified, what is unresolved, and what should not be overclaimed.")

v1, v2, v3, v4 = st.columns(4)

with v1:
    st.markdown("### Verified")
    st.write(
        "BSC mint creation, central BSC wallet routing, 0x65def and 0xc3b8 traces to zero, "
        "downstream distribution traces, Gate.io-bound route exposure, and the 5M+ old-CELL bridge/unlock route."
    )

with v2:
    st.markdown("### Unresolved")
    st.write(
        "Full reserve/backing reconciliation, exact CEX sale proceeds, exchange-internal trading, "
        "official circulating supply, and the public MEXC dumping allegation."
    )

with v3:
    st.markdown("### Current finding")
    st.write(
        "Distribution exposure is verified. Gate.io route exposure is verified. Reserve reconciliation remains open. "
        "The MEXC dumping claim remains unverified by current public on-chain evidence."
    )

with v4:
    st.markdown("### Evidence standard")
    st.write(
        "The dashboard classifies claims based on public on-chain proof, trace outputs, and public exchange labels. "
        "It does not infer CEX sale execution without exchange/account records."
    )


# ==============================
# QUICK JUMP
# ==============================

st.info("This section has been converted to Streamlit-native rendering to avoid raw HTML display.")

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

st.info("This section has been converted to Streamlit-native rendering to avoid raw HTML display.")


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
# EVIDENCE HASHES
# ==============================

hash_path = ROOT / "evidence_hashes.txt"

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Evidence Hashes</h2>
      <p>SHA-256 hashes make the evidence artifact set tamper-evident. Regenerate locally with <code>shasum -a 256 *.csv *.json *.py &gt; evidence_hashes.txt</code>.</p>
    </div>
    <span class="pill pill-green">Tamper-evident</span>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

if hash_path.exists():
    hashes = []
    for line in hash_path.read_text().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            hashes.append({"sha256": parts[0], "file": parts[-1]})
    if hashes:
        show_df(pd.DataFrame(hashes).head(200), height=420)
else:
    st.markdown(
        """
<div class="warning-note">
  <b>Missing evidence_hashes.txt:</b> Run <code>shasum -a 256 *.csv *.json *.py &gt; evidence_hashes.txt</code> and commit the file.
</div>
        """,
        unsafe_allow_html=True,
    )


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
