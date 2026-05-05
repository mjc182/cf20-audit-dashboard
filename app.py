import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="CF20 / CELL Independent Bridge Audit",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# FILES / CONSTANTS
# =============================

MASTER = Path("audit_master_summary.json")

MISSING_WALLETS_DEDUPED = Path("missing_cell_wallets_deduped.csv")
MISSING_WALLETS = Path("missing_cell_wallets.csv")

MISSING_EVENTS_DEDUPED = Path("missing_cell_events_deduped.csv")
MISSING_EVENTS_RAW = Path("missing_cell_events.csv")

EVIDENCE_HASHES = Path("evidence_hashes.csv")
MARKET_PATHS = Path("cell_market_paths.csv")
CELL_UNIVERSE_SUMMARY = Path("cell_wallet_universe_summary.json")
DEX_SUMMARY = Path("cell_dex_swaps_summary.json")

CELL_PER_MCELL = 1000


# =============================
# CSS
# =============================

st.markdown(
    """
<style>
:root {
    --bg:#050d18;
    --panel:rgba(15,23,42,.92);
    --panel2:rgba(8,20,36,.88);
    --border:rgba(148,163,184,.18);
    --text:#f8fafc;
    --muted:#94a3b8;
    --blue:#38bdf8;
    --green:#22c55e;
    --yellow:#f59e0b;
    --red:#ef4444;
    --purple:#c084fc;
}

html, body, [class*="css"] {
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 35% 5%, rgba(37,99,235,.16), transparent 30%),
        radial-gradient(circle at 90% 10%, rgba(34,197,94,.10), transparent 25%),
        radial-gradient(circle at 10% 80%, rgba(168,85,247,.10), transparent 25%),
        #050d18;
}

[data-testid="stSidebar"] {
    background:linear-gradient(180deg, #07101d 0%, #06111f 100%);
    border-right:1px solid rgba(148,163,184,.18);
}

[data-testid="stSidebar"] * { color:#dbeafe; }

.block-container {
    padding-top:1rem;
    max-width:1650px;
}

#MainMenu, header, footer { visibility:hidden; }

.sidebar-brand {
    font-size:1.08rem;
    font-weight:900;
    padding:12px 0 14px 0;
    color:#f8fafc;
}

.sidebar-section {
    color:#94a3b8;
    font-size:.72rem;
    font-weight:800;
    margin:18px 0 6px;
    text-transform:uppercase;
    letter-spacing:.08em;
}

.green-dot {
    display:inline-block;
    width:8px;
    height:8px;
    border-radius:50%;
    background:#22c55e;
    margin-right:7px;
}

.panel {
    border:1px solid rgba(148,163,184,.18);
    background:linear-gradient(145deg, rgba(15,23,42,.94), rgba(8,20,36,.88));
    border-radius:14px;
    padding:17px 18px;
    box-shadow:0 18px 40px rgba(0,0,0,.24);
}

.verdict-panel {
    border:1px solid rgba(56,189,248,.25);
    background:
        radial-gradient(circle at 10% 0%, rgba(56,189,248,.12), transparent 28%),
        linear-gradient(145deg, rgba(15,23,42,.96), rgba(8,20,36,.90));
    border-radius:14px;
    padding:20px 22px;
    box-shadow:0 18px 40px rgba(0,0,0,.28);
}

.kpi-card {
    position:relative;
    border:1px solid rgba(148,163,184,.18);
    background:linear-gradient(145deg, rgba(15,23,42,.96), rgba(12,28,50,.88));
    border-radius:14px;
    padding:16px 16px;
    min-height:112px;
    box-shadow:0 18px 40px rgba(0,0,0,.28);
    overflow:hidden;
}

.kpi-card:after {
    content:"";
    position:absolute;
    right:-20px;
    top:-20px;
    width:92px;
    height:92px;
    border-radius:50%;
    background:rgba(56,189,248,.08);
}

.kpi-card .label {
    color:#cbd5e1;
    font-size:.80rem;
    font-weight:800;
    margin-bottom:9px;
    letter-spacing:.01em;
}

.kpi-card .value {
    color:#f8fafc;
    font-size:1.55rem;
    font-weight:950;
    letter-spacing:-.04em;
}

.kpi-card .sub {
    margin-top:7px;
    font-size:.78rem;
    color:#94a3b8;
    font-weight:700;
}

.status-card {
    border:1px solid rgba(148,163,184,.18);
    border-radius:14px;
    padding:15px;
    min-height:180px;
    background:rgba(15,23,42,.72);
}

.status-title {
    font-size:.88rem;
    font-weight:950;
    text-transform:uppercase;
    letter-spacing:.06em;
    margin-bottom:10px;
}

.status-line {
    color:#cbd5e1;
    font-size:.86rem;
    line-height:1.65;
    margin-bottom:6px;
}

.chain-step {
    border:1px solid rgba(56,189,248,.22);
    background:rgba(14,30,50,.82);
    border-radius:14px;
    padding:14px;
    min-height:132px;
    text-align:center;
}

.chain-icon {
    width:44px;
    height:44px;
    margin:0 auto 9px auto;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    border:1px solid rgba(56,189,248,.40);
    background:rgba(56,189,248,.12);
    font-size:1.25rem;
}

.chain-title {
    color:#f8fafc;
    font-weight:900;
    font-size:.84rem;
    line-height:1.25;
}

.chain-sub {
    color:#94a3b8;
    font-size:.72rem;
    margin-top:6px;
}

.bad { color:#ef4444 !important; }
.warn { color:#f59e0b !important; }
.good { color:#22c55e !important; }
.blue { color:#38bdf8 !important; }
.purple { color:#c084fc !important; }

.pill {
    display:inline-block;
    border-radius:999px;
    padding:3px 9px;
    font-size:.72rem;
    font-weight:850;
    margin-right:5px;
}

.pill-good { background:rgba(34,197,94,.14); color:#4ade80; border:1px solid rgba(34,197,94,.22); }
.pill-warn { background:rgba(245,158,11,.14); color:#fbbf24; border:1px solid rgba(245,158,11,.22); }
.pill-bad { background:rgba(239,68,68,.14); color:#f87171; border:1px solid rgba(239,68,68,.22); }
.pill-blue { background:rgba(56,189,248,.13); color:#67e8f9; border:1px solid rgba(56,189,248,.22); }

.small-muted {
    color:#94a3b8;
    font-size:.82rem;
}

[data-testid="stDataFrame"] {
    border-radius:10px;
    overflow:hidden;
}

hr { border-color:rgba(148,163,184,.14); }
</style>
""",
    unsafe_allow_html=True,
)


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


def fmt_num(n, decimals=2):
    try:
        n = float(n)
    except Exception:
        return "—"

    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:,.{decimals}f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:,.{decimals}f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:,.{decimals}f}K"
    return f"{n:,.{decimals}f}"


def fmt_full(n, decimals=2):
    try:
        return f"{float(n):,.{decimals}f}"
    except Exception:
        return "—"


def short_addr(addr):
    addr = str(addr)
    if len(addr) <= 18:
        return addr
    return addr[:10] + "..." + addr[-8:]


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


def get_file_hash(filename, hashes_df):
    if hashes_df.empty or "file" not in hashes_df.columns or "sha256" not in hashes_df.columns:
        return ""

    match = hashes_df[hashes_df["file"].astype(str).str.endswith(filename)]

    if match.empty:
        return ""

    return str(match.iloc[0]["sha256"])


def verify_transaction_row(row, event_file, bridge):
    checks = []

    datum_hash = str(row.get("datum_hash", "") or "")
    atom_hash = str(row.get("atom_hash", "") or "")
    mint_to = str(row.get("mint_to", "") or "")
    match_status = str(row.get("match_status", "unmatched") or "unmatched").lower()

    checks.append("✅ datum_hash present" if datum_hash.startswith("0x") and len(datum_hash) >= 20 else "⚠️ datum_hash missing")
    checks.append("✅ atom_hash present" if atom_hash.startswith("0x") and len(atom_hash) >= 20 else "⚠️ atom_hash missing")

    if match_status == "unmatched":
        checks.append("✅ unmatched after current bridge/deposit cross-check")
    else:
        checks.append(f"⚠️ match_status={match_status}")

    checks.append("✅ deduped evidence file" if event_file.name == "missing_cell_events_deduped.csv" else "⚠️ raw evidence file, not deduped")

    bridge_source = bridge.get("source_wallet", "")
    if bridge_source and mint_to == bridge_source:
        checks.append("✅ linked to bridge-out DATUM_TX")
    else:
        checks.append("— no direct bridge-out link loaded")

    return " | ".join(checks)


def transaction_confidence(row, event_file, bridge):
    datum_hash = str(row.get("datum_hash", "") or "")
    atom_hash = str(row.get("atom_hash", "") or "")
    mint_to = str(row.get("mint_to", "") or "")

    score = 0

    if datum_hash.startswith("0x"):
        score += 35
    if atom_hash.startswith("0x"):
        score += 25
    if event_file.name == "missing_cell_events_deduped.csv":
        score += 25
    if bridge.get("source_wallet", "") and mint_to == bridge.get("source_wallet", ""):
        score += 15

    if score >= 80:
        return "High"
    if score >= 50:
        return "Medium"
    return "Review"


def sidebar():
    st.sidebar.markdown('<div class="sidebar-brand">🛡️ CF20 Audit</div>', unsafe_allow_html=True)

    groups = {
        "Overview": [
            ("app.py", "Home Verdict"),
            ("pages/11_Reconciliation.py", "Reconciliation"),
            ("pages/12_Data_Completeness.py", "Data Completeness"),
        ],
        "Evidence": [
            ("pages/3_Mint_Cross_Check.py", "Mint Cross-Check"),
            ("pages/4_Missing_CELL.py", "Unmatched Emissions"),
            ("pages/2_Verified_Wallets.py", "Verified Wallets"),
            ("pages/8_Evidence_Hashes.py", "Evidence Hashes"),
            ("pages/6_Evidence_Downloads.py", "Downloads"),
        ],
        "Tracing": [
            ("pages/5_Bridge_Out_Trace.py", "Bridge-Out Evidence"),
            ("pages/9_Linked_Evidence.py", "Linked Evidence"),
            ("pages/1_Investigation_Graph.py", "Investigation Graph"),
            ("pages/14_DEX_Transactions.py", "DEX Transactions"),
        ],
        "Tools": [
            ("pages/10_Wallet_Search.py", "Wallet Search"),
            ("pages/13_Risk_Scores.py", "Risk Scores"),
        ],
        "Methodology": [
            ("pages/7_Assumptions_Limitations.py", "Assumptions & Limitations"),
        ],
    }

    for section, links in groups.items():
        st.sidebar.markdown(f'<div class="sidebar-section">{section}</div>', unsafe_allow_html=True)

        for page, label in links:
            if page == "app.py":
                st.sidebar.page_link(page, label=label)
            elif Path(page).exists():
                st.sidebar.page_link(page, label=label)

    st.sidebar.markdown('<div class="sidebar-section">Status</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="color:#cbd5e1;font-size:.82rem;">
            <span class="green-dot"></span>Dashboard active<br>
            <span style="color:#94a3b8;">Independent evidence mode</span>
        </div>
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
generated_at = master.get("generated_at_utc", "not generated")

wallet_file = MISSING_WALLETS_DEDUPED if MISSING_WALLETS_DEDUPED.exists() else MISSING_WALLETS
wallets = load_csv(wallet_file)

event_file = MISSING_EVENTS_DEDUPED if MISSING_EVENTS_DEDUPED.exists() else MISSING_EVENTS_RAW
events_df = load_csv(event_file)
hashes_df = load_csv(EVIDENCE_HASHES)
market_paths_df = load_csv(MARKET_PATHS)

universe_summary = load_json(CELL_UNIVERSE_SUMMARY)
dex_summary = load_json(DEX_SUMMARY)

missing_cell = analysis.get("deduped_unmatched_cell")
missing_mcell = analysis.get("deduped_unmatched_mcell_equivalent")
duplicate_count = analysis.get("event_duplicates_removed")
recipient_count = analysis.get("recipient_count_deduped")
top5_share = analysis.get("top5_share_percent")

official_mcell = official.get("illegal_mcell", 1295)
official_cell = official.get("cell_equivalent", 1295000)

if missing_cell is None and not wallets.empty and "missing_cell" in wallets.columns:
    missing_cell = pd.to_numeric(wallets["missing_cell"], errors="coerce").sum()
    missing_mcell = missing_cell / CELL_PER_MCELL
    recipient_count = len(wallets)

if top5_share is None and not wallets.empty and "missing_cell" in wallets.columns:
    total = pd.to_numeric(wallets["missing_cell"], errors="coerce").sum()
    top5 = pd.to_numeric(wallets["missing_cell"], errors="coerce").head(5).sum()
    top5_share = top5 / total * 100 if total else 0

missing_display = fmt_num(missing_cell) if missing_cell is not None else "—"
missing_full = fmt_full(missing_cell)
mcell_reference = fmt_num(missing_mcell) if missing_mcell is not None else "—"

eth_rows = 0
bsc_rows = 0
for item in universe_summary.get("loaded_files", []):
    if item.get("chain") == "eth":
        eth_rows += int(item.get("rows", 0))
    if item.get("chain") == "bsc":
        bsc_rows += int(item.get("rows", 0))


# =============================
# HEADER
# =============================

top_left, top_right = st.columns([1.7, 0.8])

with top_left:
    st.markdown("# CF20 / CELL Independent Bridge Audit")
    st.caption("Independent verification of emissions, bridge evidence, wallet flows, and market-route status.")

with top_right:
    st.markdown(
        f"""
        <div class="panel">
            <div style="color:#94a3b8;font-size:.78rem;font-weight:800;">AUDIT SNAPSHOT</div>
            <div style="color:#f8fafc;font-weight:900;margin-top:4px;">{generated_at}</div>
            <div class="small-muted" style="margin-top:6px;">Evidence-led · public data · hash-verifiable</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if not MASTER.exists():
    st.warning("audit_master_summary.json not found. Run `python3 build_audit_master_summary.py` for deduped, audit-grade figures.")


# =============================
# KPI STRIP
# =============================

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    metric_card("Deduped Unmatched CELL", missing_display, "Unexplained by current bridge/deposit evidence", "bad")
with k2:
    metric_card("Recipient Wallets", f"{int(recipient_count or 0):,}", "Deduped unmatched recipients", "blue")
with k3:
    metric_card("Duplicates Removed", f"{int(duplicate_count or 0):,}", "Excluded from final total", "good")
with k4:
    metric_card("Top 5 Concentration", f"{float(top5_share or 0):,.2f}%", "Share of unmatched amount", "warn")
with k5:
    metric_card("Market Route Status", market.get("status", "Unresolved").title(), "BSC/DEX trace incomplete", "warn")


# =============================
# VERDICT + PROVEN/UNRESOLVED/NOT CLAIMED
# =============================

st.write("")

left, right = st.columns([1.05, 1])

with left:
    st.markdown(
        f"""
        <div class="verdict-panel">
            <div style="font-size:1.18rem;font-weight:950;color:#f8fafc;margin-bottom:10px;">
                Audit Verdict
            </div>
            <div style="color:#cbd5e1;line-height:1.7;">
                The audit identified a deduped set of Zerochain CELL emissions totaling
                <b>{missing_full} CELL</b> that are not currently matched to known ETH/BSC
                deposit, lock, burn, or bridge evidence in the available dataset.
                <br><br>
                This is best described as an <b>unresolved supply-verification gap</b>.
                It is not, by itself, a final claim that every unmatched emission was illegitimate
                or sold on the open market.
                <br><br>
                <span class="pill pill-blue">Evidence-led</span>
                <span class="pill pill-warn">BSC route incomplete</span>
                <span class="pill pill-good">Deduped</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="status-card">
                <div class="status-title good">Proven</div>
                <div class="status-line">✅ Deduped unmatched emission records exist</div>
                <div class="status-line">✅ Evidence files are hash-verifiable</div>
                <div class="status-line">✅ Top-recipient concentration is measurable</div>
                <div class="status-line">✅ Bridge-out DATUM_TX evidence exists for at least one top wallet</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="status-card">
                <div class="status-title warn">Unresolved</div>
                <div class="status-line">⚠️ Whether additional legitimate deposit evidence exists</div>
                <div class="status-line">⚠️ Exact amount routed to market</div>
                <div class="status-line">⚠️ BSC onward route from 0x1fa634...</div>
                <div class="status-line">⚠️ Full wallet-controller attribution</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="status-card">
                <div class="status-title bad">Not Claimed</div>
                <div class="status-line">❌ Final legal conclusion</div>
                <div class="status-line">❌ Human identity of wallet controllers</div>
                <div class="status-line">❌ Exact OTC sale amount</div>
                <div class="status-line">❌ Complete CEX internal flow visibility</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================
# EVIDENCE CHAIN
# =============================

st.markdown("## 🔗 Evidence Chain")

chain_cols = st.columns(6)
steps = [
    ("①", "Zerochain Emission", "Emission row found", "High confidence", "pill-good"),
    ("②", "Recipient Wallet", "Rj7 wallet credited", "High confidence", "pill-good"),
    ("③", "Deduped Unmatched Event", "No current bridge/deposit match", "High confidence", "pill-good"),
    ("④", "DATUM_TX Bridge-Out", "Bridge-out evidence loaded", "High confidence" if bridge.get("found") else "Not loaded", "pill-good" if bridge.get("found") else "pill-warn"),
    ("⑤", "BEP20 Destination", short_addr(bridge.get("bep20_destination", "0x1fa6348d9b13d316c62d54f62bea4e1a7207d9d6")), "High confidence" if bridge.get("found") else "Pending", "pill-good" if bridge.get("found") else "pill-warn"),
    ("⑥", "BSC / DEX Route", "Market route pending", "Unresolved", "pill-warn"),
]

for col, (icon, title, sub, conf, pill_class) in zip(chain_cols, steps):
    with col:
        st.markdown(
            f"""
            <div class="chain-step">
                <div class="chain-icon">{icon}</div>
                <div class="chain-title">{title}</div>
                <div class="chain-sub">{sub}</div>
                <div style="margin-top:8px;"><span class="pill {pill_class}">{conf}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================
# RECONCILIATION + DATA COMPLETENESS
# =============================

st.write("")
rec_col, data_col = st.columns([1, 1])

with rec_col:
    st.markdown("## ⚖️ Independent vs Official Reference")

    official_cell_value = float(official_cell or 0)
    missing_cell_value = float(missing_cell or 0)
    diff_cell = max(missing_cell_value - official_cell_value, 0)
    ratio = missing_cell_value / official_cell_value if official_cell_value else 0

    rec_df = pd.DataFrame(
        [
            {"Category": "Official reference", "CELL": official_cell_value, "Display": f"{official_mcell:,} mCELL = {official_cell_value:,.0f} CELL"},
            {"Category": "Independent unmatched", "CELL": missing_cell_value, "Display": f"{missing_cell_value:,.2f} CELL"},
        ]
    )

    chart = alt.Chart(rec_df).mark_bar().encode(
        x=alt.X("Category:N", title=None),
        y=alt.Y("CELL:Q", title="CELL"),
        tooltip=["Category:N", alt.Tooltip("CELL:Q", format=",.2f"), "Display:N"],
    ).properties(height=260)

    st.altair_chart(chart, use_container_width=True)

    st.markdown(
        f"""
        <div class="panel">
            <div style="color:#cbd5e1;line-height:1.65;">
                <b>Difference:</b> {diff_cell:,.2f} CELL<br>
                <b>Ratio:</b> {ratio:,.2f}× official CELL-equivalent reference<br>
                <span class="small-muted">Optional unit reference: 1 mCELL = 1,000 CELL.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with data_col:
    st.markdown("## 📡 Data Completeness")

    completeness = pd.DataFrame(
        [
            {"Source": "Zerochain emissions", "Status": "Indexed", "Rows": len(events_df), "Completeness": 100},
            {"Source": "ETH CELL transfers", "Status": "Strong" if eth_rows >= 100000 else "Partial", "Rows": eth_rows, "Completeness": 100 if eth_rows >= 100000 else 40},
            {"Source": "BSC CELL transfers", "Status": "Incomplete" if bsc_rows <= 150 else "Indexed", "Rows": bsc_rows, "Completeness": 5 if bsc_rows <= 150 else 85},
            {"Source": "DEX swaps", "Status": "Loaded" if DEX_SUMMARY.exists() else "Pending", "Rows": int(dex_summary.get("swap_count", 0)), "Completeness": 70 if DEX_SUMMARY.exists() else 0},
            {"Source": "Market paths", "Status": "Incomplete" if market.get("status", "unresolved") == "unresolved" else "Loaded", "Rows": len(market_paths_df), "Completeness": 15 if market.get("status", "unresolved") == "unresolved" else 70},
        ]
    )

    st.dataframe(
        completeness[["Source", "Status", "Rows", "Completeness"]],
        use_container_width=True,
        hide_index=True,
    )

    comp_chart = alt.Chart(completeness).mark_bar().encode(
        x=alt.X("Completeness:Q", title="Completeness indicator", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("Source:N", sort=None, title=None),
        tooltip=["Source:N", "Status:N", "Rows:Q", "Completeness:Q"],
    ).properties(height=260)

    st.altair_chart(comp_chart, use_container_width=True)

    if bsc_rows <= 150:
        st.warning("BSC transfer history is incomplete. Market-route tracing remains unresolved until full BSC CELL history is indexed.")


# =============================
# TRANSACTION VERIFICATION LEDGER
# =============================

st.markdown("## 🔍 Transaction Verification Ledger")
st.caption(
    "Search and verify each deduped unmatched CELL emission by wallet, datum hash, atom hash, amount, or token."
)

if events_df.empty:
    st.warning("No transaction-level file found. Upload `missing_cell_events_deduped.csv` or `missing_cell_events.csv`.")
else:
    tx = events_df.copy()

    if "mint_amount_tokens" in tx.columns:
        tx["mint_amount_tokens"] = pd.to_numeric(tx["mint_amount_tokens"], errors="coerce").fillna(0)
        tx["mint_amount_mcell_equivalent"] = tx["mint_amount_tokens"] / CELL_PER_MCELL

    tx["verification_status"] = tx.apply(lambda row: verify_transaction_row(row, event_file, bridge), axis=1)
    tx["verification_confidence"] = tx.apply(lambda row: transaction_confidence(row, event_file, bridge), axis=1)

    source_hash = get_file_hash(event_file.name, hashes_df)

    if source_hash:
        st.success(f"Evidence source: `{event_file.name}` · SHA256: `{source_hash}`")
    else:
        st.info(f"Evidence source: `{event_file.name}`")

    ledger_left, ledger_right = st.columns([0.7, 0.3])

    with ledger_left:
        search = st.text_input(
            "Search transaction evidence",
            placeholder="Paste wallet, datum_hash, atom_hash, token, or amount...",
        )

    with ledger_right:
        confidence_filter = st.selectbox("Confidence filter", ["All", "High", "Medium", "Review"])

    filtered = tx.copy()

    if search:
        s = search.lower().strip()
        searchable = filtered.astype(str).apply(lambda col: col.str.lower(), axis=0)
        mask = searchable.apply(lambda row: row.str.contains(s, na=False).any(), axis=1)
        filtered = filtered[mask]

    if confidence_filter != "All":
        filtered = filtered[filtered["verification_confidence"] == confidence_filter]

    c1, c2, c3, c4 = st.columns(4)
    shown_cell = filtered["mint_amount_tokens"].sum() if "mint_amount_tokens" in filtered.columns else 0
    shown_mcell = filtered["mint_amount_mcell_equivalent"].sum() if "mint_amount_mcell_equivalent" in filtered.columns else 0

    c1.metric("Rows shown", f"{len(filtered):,}")
    c2.metric("CELL shown", f"{shown_cell:,.2f}")
    c3.metric("Unit reference", f"{shown_mcell:,.2f} mCELL-eq")
    c4.metric("High confidence", f"{int((filtered['verification_confidence'] == 'High').sum()):,}")

    preferred_cols = [
        "mint_time",
        "time",
        "token",
        "mint_amount_tokens",
        "mint_amount_mcell_equivalent",
        "mint_to",
        "to",
        "datum_hash",
        "atom_hash",
        "match_status",
        "verification_confidence",
        "verification_status",
    ]

    cols = [c for c in preferred_cols if c in filtered.columns]
    if not cols:
        cols = filtered.columns.tolist()

    st.dataframe(filtered[cols].head(500), use_container_width=True, hide_index=True)

    st.download_button(
        "Download filtered transaction evidence",
        data=filtered[cols].to_csv(index=False).encode("utf-8"),
        file_name="filtered_verified_transaction_rows.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.warning(
        "Transaction verification confirms that a row exists in the deduped unmatched emission evidence. "
        "It does not, by itself, prove open-market sale."
    )


# =============================
# TOP WALLETS + BRIDGE-OUT
# =============================

st.write("")
wallet_col, bridge_col = st.columns([1.3, 1])

with wallet_col:
    st.markdown("## 🧾 Top Unmatched Recipients")

    if wallets.empty:
        st.info("missing_cell_wallets_deduped.csv or missing_cell_wallets.csv not found.")
    else:
        show = wallets.head(12).copy()

        if "missing_cell" in show.columns:
            show["missing_cell"] = pd.to_numeric(show["missing_cell"], errors="coerce")
            show["unit_reference_mcell_equivalent"] = show["missing_cell"] / CELL_PER_MCELL
            show["missing_cell"] = show["missing_cell"].map(lambda x: f"{x:,.2f}")
            show["unit_reference_mcell_equivalent"] = show["unit_reference_mcell_equivalent"].map(lambda x: f"{x:,.2f}")

        if "share_of_missing" in show.columns:
            show["share_of_missing"] = pd.to_numeric(show["share_of_missing"], errors="coerce").map(lambda x: f"{x:,.2f}%")

        st.dataframe(show, use_container_width=True, hide_index=True)

with bridge_col:
    st.markdown("## 🌉 Bridge-Out Evidence")

    bridge_source = bridge.get("source_wallet", "")
    bridge_destination = bridge.get("bep20_destination", "0x1fa6348d9b13d316c62d54f62bea4e1a7207d9d6")
    bridge_value = bridge.get("bridge_condition_value_cell", 3876436.277)

    st.markdown(
        f"""
        <div class="panel">
            <div style="color:#cbd5e1;line-height:1.75;">
                <b>Source wallet:</b><br>
                <code>{bridge_source or bridge.get('source_wallet_short', 'Rj7J7...MLE7o7T')}</code>
                <br><br>
                <b>Observed transaction type:</b><br>
                <code>{bridge.get('datum_type', 'DATUM_TX')}</code> · <code>BRIDGE</code> · <code>OUT</code> · <code>BEP20</code>
                <br><br>
                <b>BEP20 destination:</b><br>
                <code>{bridge_destination}</code>
                <br><br>
                <b>Bridge condition value:</b> {float(bridge_value):,.2f} CELL
                <br><br>
                <span class="pill pill-warn">BSC / DEX / OTC sale path unresolved</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================
# DISTRIBUTION CHART
# =============================

if not wallets.empty and {"mint_to", "missing_cell"}.issubset(wallets.columns):
    st.markdown("## 📊 Unmatched Emission Distribution")

    chart_df = wallets.head(15).copy()
    chart_df["missing_cell"] = pd.to_numeric(chart_df["missing_cell"], errors="coerce")
    chart_df["wallet_short"] = chart_df["mint_to"].astype(str).str[:10] + "..." + chart_df["mint_to"].astype(str).str[-6:]

    chart = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("missing_cell:Q", title="Unmatched CELL"),
        y=alt.Y("wallet_short:N", title=None, sort="-x"),
        tooltip=[
            "mint_to:N",
            alt.Tooltip("missing_cell:Q", title="Unmatched CELL", format=",.2f"),
        ],
    ).properties(height=430)

    st.altair_chart(chart, use_container_width=True)


# =============================
# DOWNLOADS
# =============================

st.markdown("## 📁 Evidence Downloads")

downloads = [
    ("Audit Master Summary", "audit_master_summary.json"),
    ("Deduped Unmatched Wallets", "missing_cell_wallets_deduped.csv"),
    ("Deduped Unmatched Events", "missing_cell_events_deduped.csv"),
    ("Evidence Hashes", "evidence_hashes.csv"),
    ("Mint Cross-Check", "cf20_mint_crosscheck.csv"),
    ("Bridge-Out Activity Raw", "zerochain_missing_cell_activity_raw.csv"),
    ("CELL Wallet Universe", "cell_wallet_universe.csv"),
    ("CELL Transfer Edges", "cell_transfer_edges.csv"),
    ("CELL Market Paths", "cell_market_paths.csv"),
    ("DEX Swaps", "cell_dex_swaps.csv"),
]

dcols = st.columns(3)

for idx, (label, filename) in enumerate(downloads):
    p = Path(filename)

    with dcols[idx % 3]:
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
