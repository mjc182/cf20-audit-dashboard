from pathlib import Path
from decimal import Decimal, InvalidOperation
import json

import pandas as pd
import streamlit as st


# ==============================
# CONFIG
# ==============================

st.set_page_config(
    page_title="CELLFRAME On-Chain Audit",
    page_icon="⬢",
    layout="wide",
    initial_sidebar_state="expanded",
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


def D(value, default="0"):
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def compact(value):
    d = D(value)
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
    return f"{D(value):,.{places}f}"


def pct(part, whole):
    whole_d = D(whole)
    if whole_d == 0:
        return "0.00%"
    return f"{(D(part) / whole_d * Decimal(100)):.2f}%"


def show_df(df, height=None):
    if df is None or df.empty:
        st.info("No artifact loaded for this table yet.")
        return

    # Streamlit/PyArrow can overflow on very large blockchain integer fields
    # such as amount_raw. Display tables are safer with object/string values.
    display_df = df.copy()

    for col in display_df.columns:
        col_l = str(col).lower()
        if (
            "raw" in col_l
            or "hash" in col_l
            or "address" in col_l
            or col_l in {"from", "to", "tx_hash", "token", "target_wallet"}
            or display_df[col].dtype == "object"
        ):
            display_df[col] = display_df[col].astype(str)

    # Also stringify Python ints that are too large for Arrow int64.
    for col in display_df.columns:
        try:
            if pd.api.types.is_integer_dtype(display_df[col]):
                max_abs = display_df[col].abs().max()
                if pd.notna(max_abs) and max_abs > 9_000_000_000_000_000_000:
                    display_df[col] = display_df[col].astype(str)
        except Exception:
            display_df[col] = display_df[col].astype(str)

    if height:
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=height)
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def artifact_table(files):
    rows = []
    for f in files:
        p = ROOT / f
        rows.append({
            "artifact": f,
            "present": "yes" if p.exists() else "no",
            "size_kb": round(p.stat().st_size / 1024, 2) if p.exists() else "",
        })
    return pd.DataFrame(rows)


# ==============================
# LOAD DATA
# ==============================

reserve = load_json(ROOT / "reserve_backing_reconciliation.json")
reserve_totals = reserve.get("totals", {}) if isinstance(reserve, dict) else {}

circ = load_json(ROOT / "circulating_supply_estimate.json")
circ_inputs = circ.get("inputs", {}) if isinstance(circ, dict) else {}
circ_estimates = circ.get("estimates", {}) if isinstance(circ, dict) else {}

old_child = load_csv(ROOT / "oldcell_458b_child_probe_summary.csv")
old_secondary = load_csv(ROOT / "oldcell_secondary_child_probe_summary.csv")
mexc_label = load_csv(ROOT / "mexc_label_check_report.csv")
mexc_pattern = load_csv(ROOT / "mexc_deposit_pattern_check_report.csv")

trace_8bbf_recipients = load_csv(ROOT / "auto_trace_8bbf_combined_recipient_summary.csv")
trace_35ce_recipients = load_csv(ROOT / "auto_trace_35ce_recipient_summary.csv")

trace_843b_recipients = load_csv(ROOT / "auto_trace_843b_recipient_summary.csv")
trace_843b_segments = load_csv(ROOT / "auto_trace_843b_segment_summary.csv")
trace_498208_recipients = load_csv(ROOT / "auto_trace_498208_partial_recipient_summary.csv")
inflows_843b_498208 = load_csv(ROOT / "inflows_843b_to_498208.csv")
circ_csv = load_csv(ROOT / "circulating_supply_estimate.csv")
mexc_market_corr = load_csv(ROOT / "mexc_cell_market_correlation_report.csv")



# ==============================
# VERIFIED VALUES
# ==============================

ETH_SUPPLY = D(reserve_totals.get("eth_total_supply_cell") or circ_inputs.get("eth_total_supply_cell") or "30300000")
BSC_SUPPLY = D(reserve_totals.get("bsc_total_supply_cell") or circ_inputs.get("bsc_total_supply_cell") or "33300000")
RAW_SUPPLY = D(circ_inputs.get("raw_eth_plus_bsc_contract_supply_cell") or "63600000")
BACKING = D(circ_estimates.get("conservative_non_circulating_cell") or "990044.19498039")
CIRC_EST = D(circ_estimates.get("conservative_circulating_supply_estimate_cell") or "62609955.80501961")
BSC_GAP = D(circ_estimates.get("bsc_supply_minus_verified_eth_backing_MEXC referenceds_cell") or "32309955.80501961")

GATEIO_EXPOSURE = D("2596567.55466338")
OLD_CELL_UNLOCK = D("5207505.2")
OLD_CELL_A9AD_HELD = D("2625551.2")

PUBLIC_MEXC_HITS = 0
if not mexc_label.empty and "status" in mexc_label.columns:
    PUBLIC_MEXC_HITS += int(
        mexc_label["status"].isin(["known_mexc_label", "bscscan_page_contains_mexc_keyword"]).sum()
    )
if not mexc_pattern.empty and "status" in mexc_pattern.columns:
    PUBLIC_MEXC_HITS += int((mexc_pattern["status"] == "known_mexc_route_detected").sum())


# ==============================
# STYLE
# ==============================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
      radial-gradient(circle at 70% 0%, rgba(32,244,232,.22), transparent 28%),
      radial-gradient(circle at 5% 8%, rgba(32,244,232,.11), transparent 28%),
      linear-gradient(180deg, #02070f 0%, #061423 52%, #02070f 100%);
    color: #f5fbff;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #061423 0%, #02070f 100%);
    border-right: 1px solid rgba(32,244,232,.18);
}

h1, h2, h3 {
    letter-spacing: -0.04em;
}

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(7,25,41,.90), rgba(4,14,26,.78));
    border: 1px solid rgba(32,244,232,.18);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 18px 70px rgba(0,0,0,.18);
}

div[data-testid="stMetric"] label {
    color: #a9bdce !important;
    font-weight: 800;
}

div[data-testid="stMetricValue"] {
    color: #20f4e8;
    font-weight: 900;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid rgba(32,244,232,.18);
}

.stTabs [data-baseweb="tab"] {
    background: rgba(7,25,41,.76);
    border: 1px solid rgba(32,244,232,.14);
    border-radius: 999px;
    padding: 10px 16px;
    color: #c9d8e5;
    font-weight: 800;
}

.stTabs [aria-selected="true"] {
    background: rgba(32,244,232,.14) !important;
    border-color: rgba(32,244,232,.45) !important;
    color: #ffffff !important;
}

.audit-card {
    background: linear-gradient(145deg, rgba(7,25,41,.88), rgba(4,14,26,.72));
    border: 1px solid rgba(32,244,232,.16);
    border-radius: 18px;
    padding: 18px;
    min-height: 145px;
}

.audit-card h3 {
    margin: 0 0 8px;
    color: #f5fbff;
}

.audit-card p {
    color: #a9bdce;
    line-height: 1.5;
}

.good {
    color: #67ffb3;
    font-weight: 900;
}

.warn {
    color: #ffe17a;
    font-weight: 900;
}

.bad {
    color: #ffa5b3;
    font-weight: 900;
}

.hero {
    background:
      radial-gradient(circle at 80% 10%, rgba(32,244,232,.20), transparent 30%),
      linear-gradient(135deg, rgba(7,25,41,.95), rgba(4,14,26,.80));
    border: 1px solid rgba(32,244,232,.22);
    border-radius: 28px;
    padding: 34px;
    margin-bottom: 22px;
    box-shadow: 0 30px 120px rgba(0,0,0,.35);
}

.hero h1 {
    font-size: clamp(2.4rem, 5vw, 5.2rem);
    line-height: .95;
    margin: 0 0 12px;
}

.hero span {
    color: #20f4e8;
}

.hero p {
    color: #c3d1de;
    max-width: 900px;
    font-size: 1.08rem;
    line-height: 1.65;
}

.route-box {
    border: 1px solid rgba(32,244,232,.18);
    border-radius: 16px;
    padding: 16px;
    background: rgba(7,25,41,.64);
    min-height: 150px;
}

.route-arrow {
    text-align: center;
    font-size: 2rem;
    color: #20f4e8;
    padding-top: 45px;
}

hr {
    border: none;
    border-top: 1px solid rgba(32,244,232,.16);
    margin: 1.4rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)


# ==============================
# SIDEBAR
# ==============================

st.sidebar.title("⬢ CELLFRAME Audit")
st.sidebar.caption("Native Streamlit tabs. No fragile anchor links.")
st.sidebar.markdown("---")
st.sidebar.markdown("**Current status**")
st.sidebar.write("✅ BSC mint route verified")
st.sidebar.write("✅ Gate.io exposure verified")
st.sidebar.write("✅ 843b → 498208 traced")
st.sidebar.write("⚠️ Reserve reconciliation open")
st.sidebar.write("⚠️ MEXC claim unverified")
st.sidebar.markdown("---")
st.sidebar.caption("Public on-chain evidence only. Not financial advice.")


# ==============================
# HERO
# ==============================

st.markdown(
    """
<div class="hero">
  <h1>CELLFRAME <span>On-Chain Audit</span></h1>
  <p>
    Independent on-chain evidence dashboard for CELL / CELLFRAME: supply tracing,
    bridge analysis, reserve MEXC referenceds, downstream wallet routing, exchange route exposure,
    and claim verification.
  </p>
</div>
""",
    unsafe_allow_html=True,
)


# ==============================
# TOP METRICS
# ==============================

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Raw ETH+BSC supply", f"{compact(RAW_SUPPLY)} CELL", "contract supply")
m2.metric("Evidence-only circulating", f"{compact(CIRC_EST)} CELL", "estimate, not official")
m3.metric("Gate.io route exposure", f"{compact(GATEIO_EXPOSURE)} CELL", "verified route")
m4.metric("Backing MEXC referenceds", f"{compact(BACKING)} CELL", "verified MEXC referenceds")
m5.metric("Public MEXC hits", f"{PUBLIC_MEXC_HITS}", "none detected")


# ==============================
# TABS
# ==============================

tabs = st.tabs([
    "Overview",
    "Findings",
    "Supply",
    "Routes",
    "Old-CELL / MEXC",
    "843b → 498208",
    "Trust",
    "Downloads",
])


# ==============================
# OVERVIEW
# ==============================

with tabs[0]:
    st.header("Executive Overview")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            """
<div class="audit-card">
<h3>Verified</h3>
<p>BSC mint creation, central BSC wallet routing, downstream distribution traces, Gate.io-bound route exposure, and old-CELL bridge/unlock.</p>
<p class="good">Evidence-backed</p>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="audit-card">
<h3>Unresolved</h3>
<p>Full reserve/backing reconciliation, exact CEX sale proceeds, official circulating supply, and the public MEXC dumping claim.</p>
<p class="warn">Open</p>
</div>
""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
<div class="audit-card">
<h3>Current finding</h3>
<p>Distribution exposure is verified. Gate.io route exposure is verified. Reserve reconciliation remains open.</p>
<p class="good">Current audit stance</p>
</div>
""",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            """
<div class="audit-card">
<h3>Evidence standard</h3>
<p>Claims are classified by public on-chain proof, trace outputs, and public exchange labels. CEX sales are not inferred.</p>
<p class="good">Audit-safe</p>
</div>
""",
            unsafe_allow_html=True,
        )

    st.subheader("Current Bridge Model")
    b1, a1, b2, a2, b3, a3, b4 = st.columns([2, .35, 2, .35, 2, .35, 2])
    with b1:
        st.markdown("### Bridge-facing wallets")
        st.write("Initial wallets interacting with bridge / lock infrastructure.")
        st.code("0x65def... / 0xc3b8...")
    with a1:
        st.markdown('<div class="route-arrow">→</div>', unsafe_allow_html=True)
    with b2:
        st.markdown("### Lock / unlock routes")
        st.write("Bridge and lock/unlock contracts on BSC and Ethereum.")
        st.code("0x35ce... / 0x7e9d...")
    with a2:
        st.markdown('<div class="route-arrow">→</div>', unsafe_allow_html=True)
    with b3:
        st.markdown("### Distribution layer")
        st.write("Downstream wallets and intermittent top-up branches.")
        st.code("0x8c85... / 0x843b...")
    with a3:
        st.markdown('<div class="route-arrow">→</div>', unsafe_allow_html=True)
    with b4:
        st.markdown("### Market endpoints")
        st.write("Labelled or high-activity custody/exchange-style endpoints.")
        st.code("Gate.io / 0x498208...")


# ==============================
# FINDINGS
# ==============================

with tabs[1]:
    st.header("Claims vs Evidence")

    findings = pd.DataFrame([
        {
            "finding": "ETH/BSC supply creation",
            "status": "verified",
            "evidence": "ETH totalSupply 30.3M and BSC totalSupply 33.3M; BSC mint event identified.",
        },
        {
            "finding": "Central BSC wallets traced",
            "status": "verified",
            "evidence": "0x65def and 0xc3b8 traced to zero; downstream branches identified.",
        },
        {
            "finding": "Gate.io route exposure",
            "status": "verified route exposure",
            "evidence": "At least 2,596,567.55 CELL routed to Gate.io-labelled custody.",
        },
        {
            "finding": "843b → 498208 branch",
            "status": "verified direct route",
            "evidence": "3.227M CELL routed from 0x843b to 0x498208 across 28 transfers.",
        },
        {
            "finding": "498208 endpoint behaviour",
            "status": "partial high-activity MEXC endpoint trace",
            "evidence": "737 events captured, 126 unique recipients, 2.103M CELL outbound before trace cap.",
        },
        {
            "finding": "Old-CELL MEXC dumping claim",
            "status": "unverified",
            "evidence": "Bridge/unlock supported; zero publicly labelled MEXC endpoints found so far.",
        },
        {
            "finding": "Reserve/backing reconciliation",
            "status": "open",
            "evidence": "Verified MEXC referenceds do not reconcile BSC supply; unresolved gap remains.",
        },
    ])
    show_df(findings)


# ==============================
# SUPPLY
# ==============================

with tabs[2]:
    st.header("Supply and Circulating Estimate")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("ETH supply", f"{fmt(ETH_SUPPLY, 0)} CELL")
    s2.metric("BSC supply", f"{fmt(BSC_SUPPLY, 0)} CELL")
    s3.metric("Raw total", f"{fmt(RAW_SUPPLY, 0)} CELL")
    s4.metric("Backing MEXC referenceds", f"{fmt(BACKING, 2)} CELL")

    st.warning(
        "The circulating estimate is evidence-only and not an official circulating supply figure. "
        "It excludes only verified reserve/backing MEXC referenceds."
    )

    s5, s6 = st.columns(2)
    s5.metric("Evidence-only circulating estimate", f"{fmt(CIRC_EST, 2)} CELL")
    s6.metric("BSC unreconciled / backing gap", f"{fmt(BSC_GAP, 2)} CELL")

    st.subheader("Circulating Supply Calculation")
    show_df(circ_csv)


# ==============================
# ROUTES
# ==============================

with tabs[3]:
    st.header("Route Evidence")

    st.subheader("BSC Mint and Gate.io Exposure Route")
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    r1.markdown("### Mint\n33.3M CELL\n`0x0000 → 0x65def`")
    r2.markdown("### Custody\n30M CELL\n`0x65def → 0xc3b8`")
    r3.markdown("### Distribution\nMultiple branches\n`0xc3b8 → recipients`")
    r4.markdown("### Consolidation\n`0xda8a` / `0x65def`")
    r5.markdown("### Gate.io\n`0x0d070...`")
    r6.markdown(f"### Exposure\n{fmt(GATEIO_EXPOSURE, 2)} CELL")

    st.success(
        f"Verified Gate.io-bound route exposure: {fmt(GATEIO_EXPOSURE, 2)} CELL. "
        "This proves route exposure, not exchange-side sale proceeds."
    )

    st.subheader("8bbf Downstream Top Recipients")
    if not trace_8bbf_recipients.empty:
        df = trace_8bbf_recipients.copy()
        if "amount_cell" in df.columns:
            df["amount_cell_num"] = pd.to_numeric(df["amount_cell"], errors="coerce")
            df = df.sort_values("amount_cell_num", ascending=False).head(25)
            df = df.drop(columns=["amount_cell_num"], errors="ignore")
        show_df(df, 420)
    else:
        st.info("8bbf recipient summary not loaded.")


# ==============================
# OLD-CELL / MEXC
# ==============================

with tabs[4]:
    st.header("Old-CELL / MEXC Claim Check")

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Old-CELL bridge/unlock", f"{compact(OLD_CELL_UNLOCK)} old CELL", "supported")
    o2.metric("0xc3b8 old-CELL final", "0", "routed onward")
    o3.metric("Largest held branch", f"{compact(OLD_CELL_A9AD_HELD)} old CELL", "0xa9ad")
    o4.metric("Public MEXC label hits", f"{PUBLIC_MEXC_HITS}", "none found")

    st.success("Supported: 5M+ old CELL was bridged/unlocked into 0xc3b8 and routed onward.")
    st.warning(
        "Not proven: the traced paths do not currently identify a publicly labelled MEXC endpoint. "
        "A private/unlabelled MEXC deposit address cannot be ruled out from public data alone."
    )

    st.subheader("Ten 100k Old-CELL Child Wallet Probe")
    show_df(old_child, 280)

    st.subheader("Secondary Child Wallet Probe")
    show_df(old_secondary, 260)

    st.subheader("Public MEXC Label Check")
    if not mexc_label.empty and {"address", "status", "bscscan_title"}.issubset(mexc_label.columns):
        show_df(mexc_label[["address", "status", "bscscan_title"]], 360)
    else:
        show_df(mexc_label, 360)

    st.subheader("MEXC Deposit-Pattern Check")
    show_df(mexc_pattern, 360)


# ==============================
# 843B / 498208
# ==============================

with tabs[5]:
    st.header("843b → 498208 Endpoint Trace")

    st.subheader("843b Downstream Branch")
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Received from 0xc3b8", "3.317M CELL", "33 inbound transfers")
    t2.metric("Routed to 0x498208", "3.227M CELL", "28 transfers")
    t3.metric("MEXC-referenced endpoint", "0x498208", "MEXC-labelled / high activity")
    t4.metric("Endpoint label status", "MEXC referenced", "public label support found")

    st.info(
        "0x843b was an intermittent downstream distribution wallet. Segmented tracing shows "
        "3.227M CELL routed to 0x498208 across 28 transfers."
    )

    st.subheader("843b Recipient Summary")
    show_df(trace_843b_recipients, 260)

    st.subheader("843b Segment Summary")
    show_df(trace_843b_segments, 320)

    st.divider()

    st.subheader("498208 MEXC-Referenced High-Activity Endpoint")

    st.success(
        "Public label upgrade: 0x4982085c9e2f89f2ecb8131eca71afad896e89cb is publicly referenced by MEXC "
        "as a BSC withdrawal address and is also labelled as MEXC 13 by public explorer/label sources. "
        "This upgrades the 843b → 498208 route from an exchange/custody-style candidate to MEXC-referenced route exposure."
    )

    st.warning(
        "Important limit: this proves MEXC-route exposure. It still does not prove exchange-internal sale execution, "
        "sale price, depositing account owner, proceeds, or final beneficiary."
    )

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Outbound captured", "2.103M CELL", "partial trace")
    e2.metric("Events captured", "737", "530 out / 207 in")
    e3.metric("Unique recipients", "126", "high activity")
    e4.metric("Balance at stop", "3.289M CELL", "trace cap reached")

    st.info(
        "0x498208 is publicly referenced by MEXC as a BSC withdrawal address and behaves like a high-activity "
        "exchange/custody endpoint, not a passive reserve wallet. The trace hit the change cap and should be treated "
        "as partial. Exchange endpoint attribution is supported by public labels; sale execution still requires "
        "exchange-side records."
    )

    st.subheader("Direct 843b → 498208 Inflows")
    show_df(inflows_843b_498208, 300)


    st.divider()

    st.subheader("MEXC Market Correlation")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deposit windows analysed", "28", "843b → 498208")
    c2.metric("Deposited to 0x498208", "3.227M CELL", "direct route")
    c3.metric("Post-window MEXC volume", "7.624M CELL", "public market data")
    c4.metric("Post/pre volume ratio", "6.46x", "average")

    st.success(
        "Public MEXC market data shows elevated CELL trading activity after the 843b → 498208 deposit windows. "
        "Across 28 deposit windows, post-deposit MEXC volume totalled 7,624,148.89 CELL and averaged 6.46x "
        "the pre-deposit window volume."
    )

    st.warning(
        "Audit limit: this supports sale-likelihood / market-impact correlation, but it still does not prove "
        "account-level exchange-internal sale execution, seller identity, sale price, proceeds, or final beneficiary "
        "without authenticated MEXC account trade records."
    )

    st.subheader("MEXC Market Correlation Report")
    show_df(mexc_market_corr, 420)


    st.subheader("498208 Partial Recipient Summary")
    show_df(trace_498208_recipients, 420)


# ==============================
# TRUST
# ==============================

with tabs[6]:
    st.header("Trust, Limits, and Verification Standard")

    
    st.info(
        "Label note: 0x498208 is treated as MEXC-referenced because MEXC publicly identified it as a BSC withdrawal address, "
        "and public explorer/label sources also label the address as MEXC 13. The dashboard still separates route exposure "
        "from exchange-side sale execution."
    )
    

    t1, t2 = st.columns(2)
    with t1:
        st.subheader("What this audit can prove")
        st.write(
            "Token creation, transfers, wallet balances, route exposure to public labelled addresses, "
            "and whether wallets behave like reserves, distributors, or high-activity endpoints."
        )
        st.subheader("What this audit does not overclaim")
        st.write(
            "CEX sale proceeds, exchange-internal trading, account owner, final beneficiary, "
            "or private/unlabelled CEX deposit attribution."
        )
    with t2:
        st.subheader("Classification standard")
        st.write("Verified = direct on-chain proof.")
        st.write("Supported = strong on-chain evidence with contextual support.")
        st.write("Unresolved = incomplete evidence or requires disclosure.")
        st.write("Unverified = not proven by current public evidence.")

    matrix = pd.DataFrame([
        {
            "evidence_type": "Token Transfer event",
            "can_prove": "movement, amount, sender, recipient, block, tx hash",
            "cannot_prove": "human intent or off-chain agreements",
        },
        {
            "evidence_type": "Wallet balance trace",
            "can_prove": "held, distributed, or reached zero",
            "cannot_prove": "legal controller without attribution evidence",
        },
        {
            "evidence_type": "Public exchange label",
            "can_prove": "exchange custody route exposure",
            "cannot_prove": "sale execution or trade price",
        },
        {
            "evidence_type": "Unlabelled wallet",
            "can_prove": "on-chain routing behaviour",
            "cannot_prove": "private CEX deposit identity",
        },
    ])
    show_df(matrix)


# ==============================
# DOWNLOADS
# ==============================

with tabs[7]:
    st.header("Evidence Downloads and Audit Artifacts")

    artifact_files = [
        "AUDIT_SUMMARY.md",
        "evidence_hashes.txt",
        "circulating_supply_estimate.json",
        "circulating_supply_estimate.csv",
        "reserve_backing_reconciliation.json",
        "reserve_backing_MEXC referenceds.csv",
        "auto_trace_c3b8_summary.json",
        "auto_trace_65def_summary.json",
        "auto_trace_da8a_summary.json",
        "auto_trace_8bbf_combined_summary.json",
        "auto_trace_35ce_summary.json",
        "auto_trace_oldcell_c3b8_summary.json",
        "auto_trace_oldcell_8929_summary.json",
        "oldcell_458b_child_probe_summary.csv",
        "oldcell_secondary_child_probe_summary.csv",
        "mexc_label_check_report.csv",
        "mexc_deposit_pattern_check_report.csv",
        "auto_trace_843b_combined_summary.json",
        "auto_trace_843b_recipient_summary.csv",
        "auto_trace_843b_segment_summary.csv",
        "inflows_843b_to_498208.csv",
        "auto_trace_498208_partial_summary.json",
        "auto_trace_498208_partial_recipient_summary.csv",
        "auto_trace_498208_partial_events.csv",
    ]

    show_df(artifact_table(artifact_files), 420)

    hash_path = ROOT / "evidence_hashes.txt"
    if hash_path.exists():
        rows = []
        for line in hash_path.read_text().splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                rows.append({"sha256": parts[0], "file": parts[-1]})
        if rows:
            st.subheader("Evidence Hashes")
            show_df(pd.DataFrame(rows), 420)
    else:
        st.warning("Missing evidence_hashes.txt. Generate it with: shasum -a 256 *.csv *.json *.py > evidence_hashes.txt")
