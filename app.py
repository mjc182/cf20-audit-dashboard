import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CF20 Audit | Home Verdict", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

MASTER = Path("audit_master_summary.json")
MISSING_WALLETS_DEDUPED = Path("missing_cell_wallets_deduped.csv")
MISSING_WALLETS = Path("missing_cell_wallets.csv")

CELL_PER_MCELL = 1000

st.markdown("""
<style>
html, body, [class*="css"] { font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif; }
[data-testid="stAppViewContainer"] { background: radial-gradient(circle at 45% 10%, rgba(37,99,235,0.15), transparent 30%), radial-gradient(circle at 90% 10%, rgba(34,197,94,0.10), transparent 25%), #050d18; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #07101d 0%, #06111f 100%); border-right: 1px solid rgba(148,163,184,0.18); }
[data-testid="stSidebar"] * { color: #dbeafe; }
.block-container { padding-top: 1rem; max-width: 1600px; }
#MainMenu, header, footer { visibility: hidden; }
.sidebar-brand { font-size:1.05rem; font-weight:900; padding:12px 0 14px 0; color:#f8fafc; }
.sidebar-section { color:#94a3b8; font-size:.72rem; font-weight:800; margin:18px 0 6px; text-transform:uppercase; }
.green-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#22c55e; margin-right:7px; }
.panel { border:1px solid rgba(148,163,184,0.18); background:linear-gradient(145deg, rgba(15,23,42,.94), rgba(8,20,36,.88)); border-radius:12px; padding:16px 17px; box-shadow:0 18px 40px rgba(0,0,0,.22); }
.kpi-card { border:1px solid rgba(148,163,184,0.18); background:linear-gradient(145deg, rgba(15,23,42,.96), rgba(12,28,50,.88)); border-radius:12px; padding:15px; min-height:104px; box-shadow:0 18px 40px rgba(0,0,0,0.28); }
.kpi-card .label { color:#cbd5e1; font-size:.82rem; font-weight:700; margin-bottom:8px; }
.kpi-card .value { color:#f8fafc; font-size:1.55rem; font-weight:900; letter-spacing:-0.04em; }
.kpi-card .sub { margin-top:6px; font-size:.78rem; color:#94a3b8; font-weight:700; }
.bad { color:#ef4444 !important; } .warn { color:#f59e0b !important; } .blue { color:#60a5fa !important; } .purple { color:#c084fc !important; }
[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

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

def metric(label, value, sub="", color=""):
    st.markdown(f'<div class="kpi-card"><div class="label">{label}</div><div class="value {color}">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)

def sidebar():
    st.sidebar.markdown('<div class="sidebar-brand">🛡️ CF20 Audit</div>', unsafe_allow_html=True)
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
        <div style="color:#cbd5e1;font-size:.82rem;">
            <span class="green-dot"></span>Dashboard active<br>
            <span style="color:#94a3b8;">Master summary preferred</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
official_cell = official.get("cell_equivalent", 1295000)

if missing_cell is None and not wallets.empty and "missing_cell" in wallets.columns:
    missing_cell = pd.to_numeric(wallets["missing_cell"], errors="coerce").sum()
    missing_mcell = missing_cell / CELL_PER_MCELL

missing_display = fmt_num(missing_cell) if missing_cell is not None else "15.8M–16.0M"
missing_mcell_display = fmt_num(missing_mcell) if missing_mcell is not None else "15.8K–16.0K"

st.markdown("# CF20 / mCELL Audit Command Center")
st.caption("Evidence-led dashboard for unmatched CELL emissions, bridge-out activity, and unresolved market tracing.")

if not MASTER.exists():
    st.warning("audit_master_summary.json not found. Run `python3 build_audit_master_summary.py` for deduped, audit-grade figures.")

st.markdown("## 🧾 Executive Verdict")
st.info(
    "Unit note: 1 mCELL = 1,000 CELL. "
    "Therefore, 1,295 mCELL equals 1,295,000 CELL-equivalent. "
    "The independent unmatched-emission estimate of approximately 15.8M–16.0M CELL equals approximately 15,800–16,000 mCELL-equivalent."
)

st.markdown(f"""
<div class="panel">
  <div style="font-size:1.22rem;font-weight:900;color:#f8fafc;margin-bottom:8px;">
    High-confidence unmatched mCELL/CELL issuance detected
  </div>
  <div style="color:#cbd5e1;line-height:1.65;">
    Independent emission matching identified approximately <b>{missing_display} CELL</b>,
    equal to approximately <b>{missing_mcell_display} mCELL-equivalent</b>,
    that could not be matched to known ETH/BSC bridge deposit flows.
    <br><br>
    The official disclosure refers to <b>{official_mcell:,} illegal mCELL</b>,
    equivalent to approximately <b>{official_cell:,.0f} CELL</b> at <b>1 mCELL = 1,000 CELL</b>.
    <br><br>
    This means the independent unmatched-emission estimate is materially larger than the official figure
    unless explained by unit interpretation, duplicate emissions, non-mCELL CELL emissions, or additional matching data.
    <br><br>
    Bridge-out evidence: <b>{'found' if bridge.get('found') else 'not loaded'}</b>.
    Market-sale quantification: <b>{market.get('status', 'unresolved')}</b>.
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")
c1,c2,c3,c4,c5 = st.columns(5)
with c1: metric("Deduped unmatched CELL", missing_display, "Master summary / current evidence", "bad")
with c2: metric("mCELL equivalent", missing_mcell_display, "CELL ÷ 1,000", "bad")
with c3: metric("Official illegal mCELL", f"{official_mcell:,}", "Cellframe statement", "warn")
with c4: metric("Official CELL-equivalent", fmt_num(official_cell), "1,295 × 1,000", "purple")
with c5: metric("Proven market sale", "Unresolved", "Requires BSC/DEX trace", "warn")

st.markdown("## ✅ Evidence Status")
st.dataframe(pd.DataFrame([
    {"Finding":"Unmatched CELL/mCELL emissions", "Status":"High confidence", "Evidence":f"{missing_display} CELL / {missing_mcell_display} mCELL-equivalent"},
    {"Finding":"Duplicate handling", "Status":"Applied if master summary exists", "Evidence":f"{duplicate_count if duplicate_count is not None else '—'} duplicate events removed"},
    {"Finding":"Official illegal mCELL disclosure", "Status":"Disclosed by Cellframe statement", "Evidence":f"{official_mcell:,} mCELL × 1,000 CELL = {official_cell:,.0f} CELL-equivalent"},
    {"Finding":"Official vs independent discrepancy", "Status":"Unresolved", "Evidence":"Independent unmatched estimate materially exceeds official 1,295 mCELL figure"},
    {"Finding":"Top unmatched wallet bridge-out", "Status":"Supported by DATUM_TX", "Evidence":"BRIDGE OUT BEP20 to 0x1fa634..."},
    {"Finding":"Sold on open market", "Status":"Not yet quantified", "Evidence":"Requires BSC/DEX/OTC destination trace"},
]), use_container_width=True, hide_index=True)

left,right = st.columns([1.35,1])
with left:
    st.markdown("## Top Unmatched CELL Recipients")
    if wallets.empty:
        st.info("missing_cell_wallets_deduped.csv or missing_cell_wallets.csv not found.")
    else:
        show = wallets.head(10).copy()
        if "missing_cell" in show.columns:
            show["missing_cell"] = pd.to_numeric(show["missing_cell"], errors="coerce")
            show["missing_mcell_equivalent"] = show["missing_cell"] / CELL_PER_MCELL
            show["missing_cell"] = show["missing_cell"].map(lambda x: f"{x:,.2f}")
            show["missing_mcell_equivalent"] = show["missing_mcell_equivalent"].map(lambda x: f"{x:,.2f}")
        if "share_of_missing" in show.columns:
            show["share_of_missing"] = pd.to_numeric(show["share_of_missing"], errors="coerce").map(lambda x: f"{x:,.2f}%")
        st.dataframe(show, use_container_width=True, hide_index=True)

with right:
    st.markdown("## Bridge-Out Evidence")
    st.markdown(f"""
- Largest unmatched wallet: `{bridge.get('source_wallet_short', 'Rj7J7...MLE7o7T')}`
- Observed transaction type: `{bridge.get('datum_type', 'DATUM_TX')}` · `BRIDGE` · `OUT` · `BEP20`
- BEP20 destination: `{bridge.get('bep20_destination', '0x1fa6348d9b13d316c62d54f62bea4e1a7207d9d6')}`
- Bridge condition value: `{bridge.get('bridge_condition_value_cell', 3876436.277):,.2f} CELL`
- Status: external-chain destination identified; BSC/DEX/OTC sale path unresolved.
""")

if not wallets.empty and {"mint_to","missing_cell"}.issubset(wallets.columns):
    st.markdown("## 📊 Unmatched CELL Distribution")
    chart_df = wallets.head(15).copy()
    chart_df["missing_cell"] = pd.to_numeric(chart_df["missing_cell"], errors="coerce")
    chart_df["missing_mcell_equivalent"] = chart_df["missing_cell"] / CELL_PER_MCELL
    chart_df["wallet_short"] = chart_df["mint_to"].astype(str).str[:10] + "..." + chart_df["mint_to"].astype(str).str[-6:]
    chart = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("missing_cell:Q", title="Unmatched CELL"),
        y=alt.Y("wallet_short:N", title=None, sort="-x"),
        tooltip=[
            "mint_to:N",
            alt.Tooltip("missing_cell:Q", title="Missing CELL", format=",.2f"),
            alt.Tooltip("missing_mcell_equivalent:Q", title="mCELL Equivalent", format=",.2f"),
        ],
    ).properties(height=420)
    st.altair_chart(chart, use_container_width=True)

st.markdown("## 📁 Evidence Downloads")
for label, filename in [
    ("Audit Master Summary","audit_master_summary.json"),
    ("Deduped Missing CELL Wallets","missing_cell_wallets_deduped.csv"),
    ("Deduped Missing CELL Events","missing_cell_events_deduped.csv"),
    ("Evidence Hashes","evidence_hashes.csv"),
    ("Missing CELL Wallets","missing_cell_wallets.csv"),
    ("Missing CELL Events","missing_cell_events.csv"),
    ("Mint Cross-Check","cf20_mint_crosscheck.csv"),
    ("Bridge-Out Activity Raw","zerochain_missing_cell_activity_raw.csv"),
]:
    p=Path(filename)
    if p.exists():
        st.download_button(f"Download {label}", p.read_bytes(), file_name=filename, mime="text/csv" if filename.endswith(".csv") else "application/json")
    else:
        st.caption(f"Missing: {filename}")
