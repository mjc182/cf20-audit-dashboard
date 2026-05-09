import json
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import altair as alt
except Exception:
    alt = None

# ==============================
# PAGE CONFIG
# ==============================

st.set_page_config(
    page_title="CF20 Audit | Independent On-Chain Evidence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================
# FILES
# ==============================

ROOT = Path(".")
MASTER = ROOT / "audit_master_summary.json"
BRIDGE_INFRA = ROOT / "bridge_infrastructure_summary.json"
BRIDGE_CLUSTER = ROOT / "bridge_cluster_summary.json"
TERMINALS = ROOT / "bridge_cluster_terminal_endpoints.csv"
UNCLASSIFIED = ROOT / "bridge_cluster_unclassified_wallets.csv"
TOTAL_SUPPLY = ROOT / "total_supply_snapshot.json"
SUPPLY_EVENTS = ROOT / "supply_events_summary.json"
VERIFIED_FINDINGS = ROOT / "verified_supply_findings.json"
VERIFIED_EDGES = ROOT / "verified_bsc_supply_edges.csv"
EVIDENCE_NOTES = ROOT / "EVIDENCE_NOTES_VERIFIED_SUPPLY_PATH.md"
WALLET_LABELS = ROOT / "known_wallet_labels.csv"
WALLET_PRIORITY = ROOT / "wallet_label_priority_review.csv"

# ==============================
# CONSTANTS
# ==============================

ETHERSCAN = "https://etherscan.io"
BSCSCAN = "https://bscscan.com"

ETH_CELL = "0x26c8afbbfe1ebaca03c2bb082e69d0476bffe099"
BSC_CELL = "0xd98438889ae7364c7e2a3540547fad042fb24642"

GATE_IO = "0x0d0707963952f2fba59dd06f2b425ace40b492fe"

# Fallback values from current investigation. These are only used if JSON files are absent.
FALLBACK_ROUTE_EXPOSURE = {
    "known_cex_routes_cell_possible": 34891274.24055864,
    "known_dex_router_routes_cell_possible": 18005549.981371474,
    "known_mev_routes_cell_possible": 7807859.89022645,
}

FALLBACK_SUPPLY = {
    "ethereum_total_supply_cell": 30300000,
    "bsc_total_supply_cell": 33300000,
    "raw_eth_plus_bsc_contract_supply_cell": 63600000,
    "verified_gateio_route_total_cell": 2596567.55466338,
    "configured_bridge_reserve_candidate_balances_cell": 1162177.99341895,
    "configured_burn_balances_cell": 565000.36437287,
}

# ==============================
# HELPERS
# ==============================

def load_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except Exception:
        return default


def load_csv(path: Path):
    try:
        return pd.read_csv(path) if path.exists() else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fnum(value, decimals=2):
    try:
        value = float(value)
    except Exception:
        return "—"
    return f"{value:,.{decimals}f}"


def compact(value):
    try:
        value = float(value)
    except Exception:
        return "—"
    abs_v = abs(value)
    if abs_v >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}B"
    if abs_v >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    if abs_v >= 1_000:
        return f"{value / 1_000:,.2f}K"
    return f"{value:,.2f}"


def short_addr(addr: str, left=6, right=4):
    if not isinstance(addr, str) or not addr.startswith("0x") or len(addr) < 12:
        return addr or "—"
    return f"{addr[:left]}...{addr[-right:]}"


def explorer_addr(addr: str, chain="eth"):
    base = BSCSCAN if chain == "bsc" else ETHERSCAN
    return f"{base}/address/{addr}"


def explorer_tx(tx: str, chain="eth"):
    base = BSCSCAN if chain == "bsc" else ETHERSCAN
    return f"{base}/tx/{tx}"


def safe_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    for col in out.columns:
        try:
            if out[col].dtype == "object":
                out[col] = out[col].astype(str)
            else:
                out[col] = out[col].replace([float("inf"), float("-inf")], None)
        except Exception:
            out[col] = out[col].astype(str)
    return out


def html_escape(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def download_if_exists(label, path, mime):
    if path.exists():
        st.download_button(
            label,
            path.read_bytes(),
            file_name=path.name,
            mime=mime,
            use_container_width=True,
        )
    else:
        st.caption(f"Missing: {path.name}")


def kpi_card(label, value, sub, icon="⬢", tone="blue"):
    st.markdown(
        f"""
        <div class="kpi-card tone-{tone}">
          <div class="kpi-top">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
          </div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-sub">{sub}</div>
          <div class="spark"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def address_chip(addr, chain="eth", label=None):
    if not addr:
        return ""
    text = html_escape(label or short_addr(addr))
    url = explorer_addr(addr, chain)
    return f'<a class="addr-chip" href="{url}" target="_blank" rel="noopener noreferrer">{text}<span>↗</span></a>'


def tx_chip(tx, chain="bsc", label="tx"):
    if not tx:
        return ""
    return f'<a class="tx-chip" href="{explorer_tx(tx, chain)}" target="_blank" rel="noopener noreferrer">{html_escape(label)} ↗</a>'


# ==============================
# DATA
# ==============================

master = load_json(MASTER)
bridge = load_json(BRIDGE_INFRA)
cluster = load_json(BRIDGE_CLUSTER)
total_supply = load_json(TOTAL_SUPPLY)
supply_events = load_json(SUPPLY_EVENTS)
verified = load_json(VERIFIED_FINDINGS)

terminals = load_csv(TERMINALS)
unclassified = load_csv(UNCLASSIFIED)
verified_edges = load_csv(VERIFIED_EDGES)

metrics = {}
metrics.update(cluster.get("cluster_metrics", {}) if isinstance(cluster.get("cluster_metrics"), dict) else {})
metrics.update(bridge.get("cluster_metrics", {}) if isinstance(bridge.get("cluster_metrics"), dict) else {})

route_cex = (
    metrics.get("known_cex_routes_cell_possible")
    or cluster.get("known_cex_routes_cell_possible")
    or bridge.get("known_cex_routes_cell_possible")
    or FALLBACK_ROUTE_EXPOSURE["known_cex_routes_cell_possible"]
)
route_dex = (
    metrics.get("known_dex_router_routes_cell_possible")
    or cluster.get("known_dex_router_routes_cell_possible")
    or bridge.get("known_dex_router_routes_cell_possible")
    or FALLBACK_ROUTE_EXPOSURE["known_dex_router_routes_cell_possible"]
)
route_mev = (
    metrics.get("known_mev_routes_cell_possible")
    or cluster.get("known_mev_routes_cell_possible")
    or bridge.get("known_mev_routes_cell_possible")
    or FALLBACK_ROUTE_EXPOSURE["known_mev_routes_cell_possible"]
)

supply_summary = verified.get("supply_summary", {}) if isinstance(verified.get("supply_summary"), dict) else {}
highlight = verified.get("highlighted_finding", {}) if isinstance(verified.get("highlighted_finding"), dict) else {}

# Read total_supply_snapshot fallback if present.
if total_supply:
    cross = total_supply.get("cross_chain_summary", {})
    if cross:
        supply_summary.setdefault(
            "raw_eth_plus_bsc_contract_supply_cell",
            cross.get("raw_contract_supply_across_indexed_chains_cell"),
        )
        supply_summary.setdefault(
            "configured_bridge_reserve_candidate_balances_cell",
            cross.get("configured_bridge_or_reserve_candidate_balance_cell"),
        )
        supply_summary.setdefault(
            "configured_burn_balances_cell",
            cross.get("configured_burn_balance_cell"),
        )

    for item in total_supply.get("chain_summaries", []):
        if item.get("status") == "ok" and item.get("chain") == "ethereum":
            supply_summary.setdefault("ethereum_total_supply_cell", item.get("total_supply_cell"))
        if item.get("status") == "ok" and item.get("chain") == "bsc":
            supply_summary.setdefault("bsc_total_supply_cell", item.get("total_supply_cell"))

eth_supply = supply_summary.get("ethereum_total_supply_cell", FALLBACK_SUPPLY["ethereum_total_supply_cell"])
bsc_supply = supply_summary.get("bsc_total_supply_cell", FALLBACK_SUPPLY["bsc_total_supply_cell"])
raw_supply = supply_summary.get("raw_eth_plus_bsc_contract_supply_cell", FALLBACK_SUPPLY["raw_eth_plus_bsc_contract_supply_cell"])
gateio_verified = (
    highlight.get("verified_gateio_route_total_cell")
    or highlight.get("amount_cell")
    or FALLBACK_SUPPLY["verified_gateio_route_total_cell"]
)
reserve_candidate_bal = supply_summary.get(
    "configured_bridge_reserve_candidate_balances_cell",
    FALLBACK_SUPPLY["configured_bridge_reserve_candidate_balances_cell"],
)
burn_bal = supply_summary.get(
    "configured_burn_balances_cell",
    FALLBACK_SUPPLY["configured_burn_balances_cell"],
)

# ==============================
# STYLE
# ==============================

st.markdown(
    """
<style>
:root {
    --bg:#050a12;
    --bg2:#07111f;
    --panel:#0a1526;
    --panel2:#081220;
    --line:rgba(56,189,248,.28);
    --line-soft:rgba(148,163,184,.18);
    --text:#f8fafc;
    --muted:#94a3b8;
    --soft:#cbd5e1;
    --cyan:#38bdf8;
    --blue:#60a5fa;
    --green:#22c55e;
    --purple:#a855f7;
    --orange:#f59e0b;
    --red:#ef4444;
}
html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stAppViewContainer"] {
    background:
      radial-gradient(circle at 8% 8%, rgba(56,189,248,.15), transparent 25%),
      radial-gradient(circle at 82% 8%, rgba(168,85,247,.14), transparent 26%),
      radial-gradient(circle at 58% 22%, rgba(34,197,94,.08), transparent 24%),
      linear-gradient(180deg, #050a12 0%, #07111f 42%, #050a12 100%);
}
[data-testid="stSidebar"], header, footer, #MainMenu { visibility:hidden; }
.block-container { max-width: 1540px; padding-top: 1rem; padding-bottom: 3rem; }

a { color: inherit; text-decoration: none; }
hr { border-color: rgba(148,163,184,.15); }

.navbar {
    position: sticky;
    top: 0;
    z-index: 100;
    margin: -1rem -1rem 1rem -1rem;
    padding: 16px 22px;
    background: rgba(3, 7, 18, .84);
    border-bottom: 1px solid rgba(56,189,248,.18);
    backdrop-filter: blur(18px);
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:20px;
}
.brand {
    display:flex;align-items:center;gap:12px;color:#f8fafc;font-weight:950;font-size:1.45rem;
}
.logo {
    width:46px;height:46px;border-radius:14px;
    display:flex;align-items:center;justify-content:center;
    color:#7dd3fc;font-weight:950;font-size:1rem;
    border:1px solid rgba(56,189,248,.55);
    background:linear-gradient(145deg, rgba(14,165,233,.18), rgba(30,41,59,.68));
    box-shadow:0 0 24px rgba(56,189,248,.28), inset 0 0 24px rgba(56,189,248,.12);
}
.navlinks { display:flex; gap:18px; align-items:center; }
.navlinks a {
    color:#cbd5e1;font-weight:800;font-size:.86rem;
    padding:8px 10px;border-radius:999px;
}
.navlinks a:hover { color:#67e8f9; background:rgba(56,189,248,.08); }
.nav-cta {
    color:#67e8f9 !important;
    border:1px solid rgba(56,189,248,.48);
    background:rgba(56,189,248,.08);
    box-shadow:0 0 18px rgba(56,189,248,.15);
}
@media (max-width: 900px) {
    .navbar { position:relative; flex-direction:column; align-items:flex-start; }
    .navlinks { flex-wrap:wrap; }
}

.hero {
    border:1px solid rgba(56,189,248,.24);
    border-radius:26px;
    overflow:hidden;
    background:
      linear-gradient(120deg, rgba(3,7,18,.98), rgba(8,20,36,.88)),
      radial-gradient(circle at 78% 45%, rgba(56,189,248,.22), transparent 32%);
    box-shadow: 0 30px 80px rgba(0,0,0,.42);
    position:relative;
}
.hero:before {
    content:"";
    position:absolute;inset:0;
    background:
      linear-gradient(rgba(56,189,248,.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,189,248,.04) 1px, transparent 1px);
    background-size: 34px 34px;
    mask-image: linear-gradient(90deg, black, transparent 85%);
    pointer-events:none;
}
.hero-inner {
    position:relative;
    display:grid;
    grid-template-columns: 1.05fr .95fr;
    gap:28px;
    padding:44px 42px;
}
@media (max-width: 1050px) {
    .hero-inner { grid-template-columns:1fr; padding:32px 24px; }
}
.eyebrow {
    display:inline-flex;align-items:center;gap:8px;
    border:1px solid rgba(34,197,94,.30);
    background:rgba(5,46,22,.34);
    color:#86efac;
    padding:7px 12px;border-radius:999px;
    font-weight:900;font-size:.78rem;
    margin-bottom:16px;
}
.hero h1 {
    margin:0;
    color:#f8fafc;
    font-size: clamp(2.5rem, 6vw, 5.8rem);
    line-height:.92;
    letter-spacing:-.07em;
}
.gradient-text {
    display:block;
    background:linear-gradient(90deg, #38bdf8, #60a5fa 32%, #a855f7 72%, #f59e0b);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    text-shadow:0 0 38px rgba(56,189,248,.18);
}
.hero-copy {
    color:#cbd5e1;
    max-width:720px;
    line-height:1.65;
    font-size:1.04rem;
    margin:20px 0 24px;
}
.cta-row { display:flex; gap:12px; flex-wrap:wrap; }
.btn {
    display:inline-flex;align-items:center;gap:9px;
    padding:13px 18px;border-radius:13px;
    font-weight:950;letter-spacing:.01em;
}
.btn-primary {
    color:#e0f2fe;
    border:1px solid rgba(56,189,248,.55);
    background:linear-gradient(145deg, rgba(14,165,233,.20), rgba(30,41,59,.58));
    box-shadow:0 0 25px rgba(56,189,248,.22);
}
.btn-secondary {
    color:#e9d5ff;
    border:1px solid rgba(168,85,247,.45);
    background:rgba(88,28,135,.18);
}
.holo {
    min-height:390px;
    border:1px solid rgba(56,189,248,.20);
    border-radius:24px;
    background:
      radial-gradient(circle at 50% 55%, rgba(56,189,248,.35), transparent 26%),
      radial-gradient(circle at 50% 55%, rgba(168,85,247,.18), transparent 42%),
      rgba(8,20,36,.26);
    position:relative;
    display:flex;align-items:center;justify-content:center;
    overflow:hidden;
}
.holo:before {
    content:"";
    position:absolute;width:440px;height:440px;border-radius:999px;
    border:1px solid rgba(56,189,248,.35);
    box-shadow:0 0 50px rgba(56,189,248,.16), inset 0 0 60px rgba(56,189,248,.08);
    animation:pulse 4s infinite ease-in-out;
}
.holo:after {
    content:"";
    position:absolute;width:620px;height:180px;border-radius:50%;
    border:1px solid rgba(56,189,248,.24);
    bottom:54px;
    box-shadow:0 0 40px rgba(56,189,248,.10);
}
@keyframes pulse { 0%,100% { transform:scale(.96); opacity:.68 } 50% { transform:scale(1.03); opacity:1 } }
.holo-core {
    width:180px;height:180px;border-radius:34px;
    border:2px solid rgba(56,189,248,.65);
    display:flex;align-items:center;justify-content:center;
    color:#7dd3fc;font-size:3.2rem;font-weight:950;line-height:.9;text-align:center;
    background:rgba(8,20,36,.62);
    box-shadow:0 0 40px rgba(56,189,248,.45), inset 0 0 40px rgba(56,189,248,.16);
}
.float-card {
    position:absolute;
    border:1px solid rgba(148,163,184,.20);
    background:rgba(8,20,36,.74);
    border-radius:16px;padding:16px;
    color:#cbd5e1;line-height:1.6;font-size:.88rem;
    box-shadow:0 18px 40px rgba(0,0,0,.20);
}
.float-card b { color:#67e8f9; }
.float-left { left:28px; top:90px; }
.float-right { right:28px; top:105px; border-color:rgba(168,85,247,.30); }
.float-right b { color:#d8b4fe; }

.kpi-grid {
    margin-top:18px;
    display:grid;
    grid-template-columns: repeat(6, minmax(150px, 1fr));
    gap:12px;
}
@media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 700px) { .kpi-grid { grid-template-columns: 1fr; } }
.kpi-card {
    border:1px solid rgba(56,189,248,.22);
    background:linear-gradient(145deg, rgba(15,23,42,.95), rgba(8,20,36,.86));
    border-radius:18px;
    padding:17px;
    min-height:145px;
    position:relative;
    overflow:hidden;
    box-shadow:0 18px 46px rgba(0,0,0,.28);
}
.kpi-card:before {
    content:"";
    position:absolute;inset:-1px;
    background:linear-gradient(135deg, rgba(56,189,248,.14), transparent 45%);
    pointer-events:none;
}
.tone-purple { border-color:rgba(168,85,247,.35); }
.tone-orange { border-color:rgba(245,158,11,.35); }
.tone-green { border-color:rgba(34,197,94,.35); }
.tone-red { border-color:rgba(239,68,68,.35); }
.kpi-top { display:flex;gap:10px;align-items:center;position:relative;z-index:1; }
.kpi-icon { color:#67e8f9;font-size:1.3rem; }
.kpi-label { color:#cbd5e1;font-size:.80rem;font-weight:900;line-height:1.3; }
.kpi-value { position:relative;z-index:1;color:#f8fafc;font-size:1.85rem;font-weight:950;letter-spacing:-.055em;margin-top:10px; }
.kpi-sub { position:relative;z-index:1;color:#94a3b8;font-size:.75rem;font-weight:750;line-height:1.4;margin-top:5px; }
.spark {
    position:absolute;left:14px;right:14px;bottom:14px;height:22px;
    opacity:.5;
    background:
      linear-gradient(135deg, transparent 0 12%, rgba(56,189,248,.6) 12% 14%, transparent 14% 26%, rgba(56,189,248,.5) 26% 28%, transparent 28% 41%, rgba(56,189,248,.7) 41% 43%, transparent 43% 58%, rgba(56,189,248,.55) 58% 60%, transparent 60% 75%, rgba(56,189,248,.6) 75% 77%, transparent 77%);
}

.section {
    margin-top:26px;
    border:1px solid rgba(148,163,184,.16);
    background:linear-gradient(145deg, rgba(15,23,42,.92), rgba(8,20,36,.82));
    border-radius:22px;
    padding:22px;
    box-shadow:0 20px 55px rgba(0,0,0,.24);
}
.section-title {
    display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:16px;
}
.section-title h2 {
    margin:0;color:#f8fafc;font-size:1.7rem;letter-spacing:-.04em;line-height:1.1;
}
.section-title p {
    margin:6px 0 0;color:#94a3b8;line-height:1.55;font-size:.94rem;
}
.badge {
    display:inline-flex;align-items:center;gap:7px;
    border-radius:999px;padding:7px 11px;
    border:1px solid rgba(34,197,94,.35);
    background:rgba(5,46,22,.28);
    color:#86efac;font-weight:900;font-size:.78rem;white-space:nowrap;
}
.badge.orange { color:#fcd34d;background:rgba(51,31,5,.28);border-color:rgba(245,158,11,.36); }
.badge.blue { color:#7dd3fc;background:rgba(8,47,73,.30);border-color:rgba(56,189,248,.36); }
.badge.purple { color:#d8b4fe;background:rgba(59,7,100,.25);border-color:rgba(168,85,247,.36); }

.bridge-flow {
    display:grid;
    grid-template-columns: repeat(5, minmax(180px, 1fr));
    gap:16px;
    align-items:stretch;
    position:relative;
}
@media (max-width: 1100px) { .bridge-flow { grid-template-columns:1fr; } }
.flow-card {
    border:1px solid rgba(56,189,248,.34);
    border-radius:18px;
    background:rgba(8,20,36,.66);
    padding:18px 16px;
    min-height:360px;
    position:relative;
    overflow:hidden;
}
.flow-card:before {
    content:"";
    position:absolute;inset:0;
    background:radial-gradient(circle at 50% 25%, rgba(56,189,248,.20), transparent 35%);
    pointer-events:none;
}
.flow-card.purple { border-color:rgba(168,85,247,.48); }
.flow-card.green { border-color:rgba(34,197,94,.48); }
.flow-card.orange { border-color:rgba(245,158,11,.52); }
.flow-num {
    display:inline-flex;align-items:center;justify-content:center;
    width:42px;height:42px;border-radius:13px;
    border:1px solid rgba(56,189,248,.45);
    color:#67e8f9;font-weight:950;font-size:1.05rem;
    background:rgba(14,165,233,.12);
}
.flow-card h3 { color:#f8fafc;font-size:1.05rem;margin:14px 0 12px;letter-spacing:-.02em; }
.flow-icon {
    width:70px;height:70px;border-radius:999px;margin:8px auto 14px;
    display:flex;align-items:center;justify-content:center;
    border:1px solid rgba(56,189,248,.40);
    background:rgba(8,20,36,.72);
    box-shadow:0 0 28px rgba(56,189,248,.20);
    color:#7dd3fc;font-size:2rem;
}
.status-pill {
    display:block;text-align:center;margin:0 auto 16px;
    max-width:130px;border-radius:999px;padding:7px 10px;
    border:1px solid rgba(56,189,248,.35);
    background:rgba(8,47,73,.30);
    color:#7dd3fc;font-weight:950;font-size:.80rem;
}
.flow-list { margin:0 0 16px 0;padding-left:16px;color:#cbd5e1;line-height:1.55;font-size:.88rem; }
.addr-stack { display:flex;flex-direction:column;gap:8px;margin-top:auto;position:relative;z-index:1; }
.addr-chip, .tx-chip {
    display:flex;align-items:center;justify-content:space-between;gap:9px;
    border:1px solid rgba(56,189,248,.30);
    background:rgba(2,8,23,.45);
    color:#67e8f9;
    border-radius:10px;
    padding:8px 10px;
    font-weight:900;
    font-size:.80rem;
    font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.addr-chip:hover, .tx-chip:hover { border-color:rgba(56,189,248,.70); background:rgba(14,165,233,.14); }
.flow-arrow {
    display:none;
}
@media (min-width: 1101px) {
    .flow-card:not(:last-child):after {
        content:"";
        position:absolute;
        right:-20px;
        top:45%;
        width:42px;height:42px;
        border-top:4px solid rgba(56,189,248,.80);
        border-right:4px solid rgba(56,189,248,.80);
        transform:rotate(45deg);
        filter:drop-shadow(0 0 12px rgba(56,189,248,.8));
        z-index:4;
    }
}

.timeline {
    display:flex;flex-direction:column;gap:12px;
}
.timeline-row {
    display:grid;
    grid-template-columns: 68px 1fr auto;
    gap:14px;
    align-items:center;
    border:1px solid rgba(148,163,184,.14);
    background:rgba(2,8,23,.30);
    border-radius:14px;
    padding:12px 14px;
}
@media (max-width: 800px) { .timeline-row { grid-template-columns:1fr; } }
.timeline-step {
    width:42px;height:42px;border-radius:999px;
    display:flex;align-items:center;justify-content:center;
    color:#86efac;background:rgba(22,101,52,.26);
    border:1px solid rgba(34,197,94,.38);
    font-weight:950;
}
.timeline-main b { color:#f8fafc; }
.timeline-main div { color:#cbd5e1;line-height:1.55;font-size:.88rem;margin-top:2px; }
.timeline-meta { display:flex;flex-direction:column;gap:6px;align-items:flex-end; }
@media (max-width: 800px) { .timeline-meta { align-items:flex-start; } }

.exposure-row {
    display:grid;grid-template-columns:1fr;gap:14px;
}
.exposure-card {
    border:1px solid rgba(148,163,184,.14);
    background:rgba(2,8,23,.34);
    border-radius:16px;padding:15px;
}
.exposure-head { display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:10px; }
.exposure-label { color:#cbd5e1;font-weight:950; }
.exposure-value { color:#f8fafc;font-size:1.35rem;font-weight:950;letter-spacing:-.03em; }
.bar {
    height:10px;border-radius:999px;background:rgba(148,163,184,.13);overflow:hidden;
}
.bar span { display:block;height:100%;border-radius:999px;background:linear-gradient(90deg, #22c55e, #86efac); }
.bar.purple span { background:linear-gradient(90deg, #a855f7, #d8b4fe); }
.bar.orange span { background:linear-gradient(90deg, #f59e0b, #fcd34d); }

.note {
    border:1px solid rgba(245,158,11,.36);
    background:rgba(51,31,5,.32);
    color:#fde68a;
    border-radius:16px;padding:15px;line-height:1.65;
}
.success-note {
    border:1px solid rgba(34,197,94,.34);
    background:rgba(5,46,22,.26);
    color:#bbf7d0;
    border-radius:16px;padding:15px;line-height:1.65;
}
.muted { color:#94a3b8; }
.small { font-size:.84rem;line-height:1.55; }
.footer {
    margin-top:26px;
    border:1px solid rgba(148,163,184,.14);
    border-radius:18px;padding:18px;
    background:rgba(2,8,23,.35);
    display:grid;
    grid-template-columns: repeat(4, 1fr);
    gap:12px;
}
.footer-item { color:#cbd5e1;font-size:.86rem;line-height:1.55; }
.footer-item b { color:#7dd3fc;display:block;margin-bottom:4px; }
@media (max-width: 900px) { .footer { grid-template-columns:1fr; } }

[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow:hidden;
    border:1px solid rgba(148,163,184,.12);
}
div[data-testid="stMetric"] {
    background: rgba(2,8,23,.32);
    border: 1px solid rgba(148,163,184,.14);
    border-radius: 16px;
    padding: 14px 16px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================
# NAV
# ==============================

st.markdown(
    """
<div class="navbar">
  <div class="brand"><div class="logo">CF<br>20</div><span>CF20 Audit</span></div>
  <div class="navlinks">
    <a href="#overview">Overview</a>
    <a href="#bridge-model">Bridge Model</a>
    <a href="#verified-supply">Verified Supply</a>
    <a href="#bsc-path">BSC Supply Path</a>
    <a href="#primary-custody-trace">Custody Trace</a>
    <a href="#reserve-backing">Reserve Backing</a>
    <a href="#evidence">Evidence</a>
    <a class="nav-cta" href="#downloads">Download Evidence</a>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ==============================
# HERO
# ==============================

st.markdown('<a id="overview"></a>', unsafe_allow_html=True)

st.markdown(
    f"""
<div class="hero">
  <div class="hero-inner">
    <div>
      <div class="eyebrow">● On-chain verified evidence package</div>
      <h1>Independent<br>On-Chain Audit of <span class="gradient-text">CF20 / CELL</span></h1>
      <div class="hero-copy">
        Bridge infrastructure has been identified, market-route exposure has been mapped,
        and verified supply evidence now connects BSC mint creation to exchange custody infrastructure.
        This site separates <b>contract supply</b>, <b>route exposure</b>, and <b>unresolved reserve backing</b>.
      </div>
      <div class="cta-row">
        <a class="btn btn-primary" href="#bsc-path">▣ View verified path</a>
        <a class="btn btn-secondary" href="#verified-supply">⛓ See supply audit</a>
      </div>
    </div>
    <div class="holo">
      <div class="float-card float-left"><b>ON-CHAIN</b><br>Transparent<br>Verifiable<br>Reproducible</div>
      <div class="holo-core">CF<br>20</div>
      <div class="float-card float-right"><b>INDEPENDENT</b><br>No team keys<br>No off-chain claims<br>Evidence-first</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ==============================
# KPI GRID
# ==============================

st.markdown(
    f"""
<div class="kpi-grid">
""",
    unsafe_allow_html=True,
)
cols = st.columns(6)
with cols[0]:
    kpi_card("Raw ETH+BSC contract supply", f"{compact(raw_supply)}", "Contract-level supply, not consolidated circulation", "⬡", "blue")
with cols[1]:
    kpi_card("Ethereum supply", f"{compact(eth_supply)}", "One verified ETH mint event", "◆", "purple")
with cols[2]:
    kpi_card("BSC supply", f"{compact(bsc_supply)}", "One verified BSC mint event", "⬢", "orange")
with cols[3]:
    kpi_card("Verified Gate.io route", f"{compact(gateio_verified)}", "BSC mint path to Gate.io-labelled endpoint", "▣", "green")
with cols[4]:
    kpi_card("CEX route exposure", f"{compact(route_cex)}", "Known labelled CEX route exposure", "🏦", "green")
with cols[5]:
    kpi_card("DEX / MEV exposure", f"{compact(float(route_dex) + float(route_mev))}", "Router + MEV route exposure", "↔", "orange")
st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# BRIDGE MODEL
# ==============================

st.markdown('<a id="bridge-model"></a>', unsafe_allow_html=True)
st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Current Bridge Model</h2>
      <p>Observed bridge infrastructure and downstream routing paths, displayed as live website components with explorer links.</p>
    </div>
    <div class="badge">● Audit evidence: on-chain verified</div>
  </div>
  <div class="bridge-flow">
""",
    unsafe_allow_html=True,
)

flow_cards = [
    {
        "num": "01",
        "title": "Bridge-Facing Wallets",
        "icon": "💼",
        "status": "Identified",
        "tone": "",
        "items": ["Externally owned / bridge-facing wallets", "Bridge entry points", "High-value fund receipt"],
        "chips": [
            ("0x4a831a8ebb160ad025d34a788c99e9320b9ab531", "eth"),
            ("0xfd64fa5976687c2048f08f5df89c9a78e31df680", "eth"),
        ],
    },
    {
        "num": "02",
        "title": "Lock / Unlock Contracts",
        "icon": "🔒",
        "status": "Supported",
        "tone": "purple",
        "items": ["Lock Token method observed", "Unlock Token method observed", "Bridge Token routing observed"],
        "chips": [
            ("0xfd64fa5976687c2048f08f5df89c9a78e31df680", "eth"),
            ("0x4a831a8ebb160ad025d34a788c99e9320b9ab531", "eth"),
        ],
    },
    {
        "num": "03",
        "title": "Intake / Aggregator Layer",
        "icon": "▱",
        "status": "Observed",
        "tone": "",
        "items": ["Intake of released assets", "Aggregation and batching", "Pre-routing staging layer"],
        "chips": [
            ("0x35ce1677d3d6aaaacd96510704d3c8617a12ee60", "eth"),
            ("0x50ebb0827aa80ba1a2a30b38581629996262d481", "eth"),
            ("0x65def3ea531fd80354ec11c611ae4faa06068f27", "eth"),
        ],
    },
    {
        "num": "04",
        "title": "Consolidation / Routing",
        "icon": "↱",
        "status": "Observed",
        "tone": "green",
        "items": ["Consolidation of flows", "Routing optimization", "Multi-path distribution"],
        "chips": [
            ("0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5", "eth"),
            ("0x9c4cc862f51b1ba90485de3502aa058ca4331f32", "eth"),
            ("0xd3ec4a0113091ed2b0a3edbfdf1476efe07c8539", "eth"),
        ],
    },
    {
        "num": "05",
        "title": "Market Endpoints",
        "icon": "◎",
        "status": "Observed",
        "tone": "orange",
        "items": ["CEX deposit endpoints", "DEX liquidity and router hubs", "Swap aggregator routes"],
        "chips": [
            (GATE_IO, "eth", "Gate.io 1"),
            ("0x3cc936b795a188f0e246cbb2d74c5bd190aecf18", "eth", "MEXC 3"),
            ("0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad", "eth", "Uniswap Router"),
            ("0x1111111254eeb25477b68fb85ed929f73a960582", "eth", "1inch Router"),
        ],
    },
]

for card in flow_cards:
    lis = "".join([f"<li>{html_escape(item)}</li>" for item in card["items"]])
    chips = "".join([address_chip(*chip) for chip in card["chips"]])
    st.markdown(
        f"""
    <div class="flow-card {card["tone"]}">
      <div class="flow-num">{card["num"]}</div>
      <h3>{html_escape(card["title"])}</h3>
      <div class="flow-icon">{card["icon"]}</div>
      <div class="status-pill">{card["status"]}</div>
      <ul class="flow-list">{lis}</ul>
      <div class="addr-stack">{chips}</div>
    </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
  </div>
  <div style="margin-top:18px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
    <div class="success-note"><b>Observed on-chain</b><br>Direct on-chain evidence found and verified during audit.</div>
    <div class="success-note"><b>Supported classification</b><br>Strong correlation with known bridge infrastructure patterns.</div>
    <div class="note"><b>Unresolved final sale</b><br>Final market execution is not fully observable after CEX deposit.</div>
    <div class="success-note"><b>Explorer-linked</b><br>Addresses link directly to Etherscan or BscScan.</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ==============================
# SUPPLY SECTION
# ==============================

st.markdown('<a id="verified-supply"></a>', unsafe_allow_html=True)

eth_minted = supply_summary.get("ethereum_minted_cell", eth_supply)
bsc_minted = supply_summary.get("bsc_minted_cell", bsc_supply)
eth_dead = supply_summary.get("ethereum_transferred_to_dead_cell", 565000.00009071)
bsc_burn = supply_summary.get("bsc_burn_to_zero_cell", 0)

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Verified Supply</h2>
      <p>Contract-level supply creation is verified separately from market-route exposure and reserve backing.</p>
    </div>
    <div class="badge blue">Supply creation verified</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

s1, s2, s3 = st.columns([1, 1, 1])
with s1:
    st.markdown(
        f"""
<div class="section" style="margin-top:0;">
  <div class="badge purple">Ethereum</div>
  <h3 style="color:#f8fafc;margin:14px 0 6px;">30.3M CELL supply</h3>
  <p class="small muted">Ethereum CELL supply is explained by one verified mint event.</p>
  <div class="success-note">
    Minted: <b>{fnum(eth_minted)} CELL</b><br>
    Burn-to-zero: <b>0 CELL</b><br>
    Sent to dead address: <b>{fnum(eth_dead)} CELL</b>
  </div>
  <br>
  {address_chip(ETH_CELL, "eth", "ETH CELL token")}
</div>
        """,
        unsafe_allow_html=True,
    )

with s2:
    st.markdown(
        f"""
<div class="section" style="margin-top:0;">
  <div class="badge orange">BSC</div>
  <h3 style="color:#f8fafc;margin:14px 0 6px;">33.3M CELL supply</h3>
  <p class="small muted">BSC CELL supply is explained by one verified mint event to 0x65def...</p>
  <div class="success-note">
    Minted: <b>{fnum(bsc_minted)} CELL</b><br>
    Burn-to-zero: <b>{fnum(bsc_burn)} CELL</b><br>
    Mint recipient: <b>0x65def...68f27</b>
  </div>
  <br>
  {address_chip(BSC_CELL, "bsc", "BSC CELL token")}
</div>
        """,
        unsafe_allow_html=True,
    )

with s3:
    st.markdown(
        f"""
<div class="section" style="margin-top:0;">
  <div class="badge">Interpretation</div>
  <h3 style="color:#f8fafc;margin:14px 0 6px;">Raw supply is not circulation</h3>
  <p class="small muted">ETH+BSC totalSupply is a raw contract-level number. Consolidated economic supply still requires lock/reserve reconciliation.</p>
  <div class="note">
    Raw ETH+BSC supply: <b>{fnum(raw_supply)} CELL</b><br>
    Configured reserve candidates: <b>{fnum(reserve_candidate_bal)} CELL</b><br>
    Configured burn balances: <b>{fnum(burn_bal)} CELL</b>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

# ==============================
# BSC SUPPLY PATH
# ==============================

st.markdown('<a id="bsc-path"></a>', unsafe_allow_html=True)

st.markdown(
    f"""
<div class="section">
  <div class="section-title">
    <div>
      <h2>Verified BSC Supply Path</h2>
      <p>The BSC supply path now has a verified route from the mint event into a Gate.io-labelled endpoint.</p>
    </div>
    <div class="badge orange">Verified Gate.io route: {compact(gateio_verified)} CELL</div>
  </div>
""",
    unsafe_allow_html=True,
)

# Preferred: use verified_bsc_supply_edges.csv. Fallback: hardcoded edges from investigation.
if verified_edges.empty:
    fallback_edges = [
        {"step": "01", "block_number": "21943290", "from": "0x0000000000000000000000000000000000000000", "to": "0x65def3ea531fd80354ec11c611ae4faa06068f27", "amount_cell": "33300000", "tx_hash": "0xfe69b4b4ebcf695cb57153d0d06959417c185ad1051b0d91cd4114356ea44287", "classification": "mint", "finding": "Full BSC supply minted to 0x65def..."},
        {"step": "02", "block_number": "21943418", "from": "0x65def3ea531fd80354ec11c611ae4faa06068f27", "to": "0xc3b8a652e59d59a71b00808c1fb2432857080ab8", "amount_cell": "30000000", "tx_hash": "0x51a94ce1f6c5fb79471607d9770bda9ff03adbd64d26d8e68494f2ff3bccb829", "classification": "primary custody", "finding": "30M CELL moved to primary custody wallet."},
        {"step": "08", "block_number": "33936560", "from": "0xc3b8a652e59d59a71b00808c1fb2432857080ab8", "to": "0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5", "amount_cell": "500000", "tx_hash": "0x59c9d092737c8822c82842fdf70333e8dc22b39fa5d881c51f6f5b0fd7f93550", "classification": "cross-cluster link", "finding": "500k CELL sent to 0xda8a..."},
        {"step": "09", "block_number": "33943897", "from": "0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5", "to": GATE_IO, "amount_cell": "500000", "tx_hash": "0x032a50cc99cc3ea7388f229ec4c820783dfcc9dc2a1e94cbc8a12518d9a52f7d", "classification": "CEX route", "finding": "500k CELL routed to Gate.io-labelled endpoint."},
        {"step": "11", "block_number": "34655452", "from": "0xc3b8a652e59d59a71b00808c1fb2432857080ab8", "to": "0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5", "amount_cell": "500000", "tx_hash": "0xae0f28a654b7f34f9ce6104f39836088123b80fa1f8f928886763a90013f2830", "classification": "cross-cluster link", "finding": "Second 500k CELL sent to 0xda8a..."},
        {"step": "12", "block_number": "34691012", "from": "0xda8a4204de68f959ca2302c4febc4ee5b6cc32f5", "to": GATE_IO, "amount_cell": "500000", "tx_hash": "0xb1609fb3b9536e772b396d642939be5dadb6abadb490aa5f025b9dbcd733e021", "classification": "CEX route", "finding": "Second 500k CELL route to Gate.io-labelled endpoint."},
    ]
    edges_display = pd.DataFrame(fallback_edges)
else:
    edges_display = verified_edges.copy()

# Sort by step.
try:
    edges_display["_step_num"] = pd.to_numeric(edges_display["step"], errors="coerce")
    edges_display = edges_display.sort_values("_step_num")
except Exception:
    pass

# Show most important rows as cards.
important_steps = {"01", "02", "05", "06", "07", "08", "09", "10", "11", "12"}
display_rows = []
for _, row in edges_display.iterrows():
    step = str(row.get("step", "")).zfill(2)
    if step in important_steps:
        display_rows.append(row)

for _, row in pd.DataFrame(display_rows).iterrows():
    step = str(row.get("step", ""))
    amount = fnum(row.get("amount_cell"))
    tx = str(row.get("tx_hash", ""))
    from_addr = str(row.get("from", ""))
    to_addr = str(row.get("to", ""))
    finding = html_escape(row.get("finding", ""))
    classification = html_escape(row.get("classification", ""))

    st.markdown(
        f"""
<div class="timeline-row">
  <div class="timeline-step">{step}</div>
  <div class="timeline-main">
    <b>{amount} CELL · {classification}</b>
    <div>{finding}</div>
    <div class="muted small">Block {html_escape(row.get("block_number", ""))}</div>
  </div>
  <div class="timeline-meta">
    {address_chip(from_addr, "bsc", "from " + short_addr(from_addr))}
    {address_chip(to_addr, "bsc", "to " + short_addr(to_addr))}
    {tx_chip(tx, "bsc", "view tx") if tx.startswith("0x") else ""}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# PRIMARY BSC CUSTODY WALLET TRACE
# ==============================

custody_summary = load_json(Path("auto_trace_wallet_summary.json"))
custody_recipients = load_csv(Path("auto_trace_wallet_recipient_summary.csv"))

st.markdown('<a id="primary-custody-trace"></a>', unsafe_allow_html=True)

if custody_summary:
    complete = custody_summary.get("complete_trace_result", {})
    target_wallet = complete.get("target_wallet") or custody_summary.get("target_wallet", "0xc3b8a652e59d59a71b00808c1fb2432857080ab8")

    st.markdown(
        f"""
<div class="section">
  <div class="section-title">
    <div>
      <h2>Primary BSC Custody Wallet: Traced to Zero</h2>
      <p>The wallet that received 30M CELL shortly after the BSC mint has now been traced through its balance changes to zero.</p>
    </div>
    <div class="badge">Trace complete</div>
  </div>

  <div class="kpi-grid" style="grid-template-columns:repeat(5,1fr);">
    <div class="kpi-card tone-blue">
      <div class="kpi-label">Target wallet</div>
      <div class="kpi-value" style="font-size:1.05rem;">0xc3b8...0ab8</div>
      <div class="kpi-sub">Primary BSC custody wallet</div>
    </div>
    <div class="kpi-card tone-green">
      <div class="kpi-label">Final balance</div>
      <div class="kpi-value">{compact(complete.get("final_balance_cell", custody_summary.get("current_balance_cell", 0)))} CELL</div>
      <div class="kpi-sub">Trace reached zero balance</div>
    </div>
    <div class="kpi-card tone-orange">
      <div class="kpi-label">Outbound traced</div>
      <div class="kpi-value">{compact(complete.get("total_outbound_cell", 0))}</div>
      <div class="kpi-sub">Auto-traced outbound segment</div>
    </div>
    <div class="kpi-card tone-purple">
      <div class="kpi-label">Unique recipients</div>
      <div class="kpi-value">{complete.get("unique_recipients", "—")}</div>
      <div class="kpi-sub">Recipient wallets in completed trace</div>
    </div>
    <div class="kpi-card tone-blue">
      <div class="kpi-label">Outbound events</div>
      <div class="kpi-value">{complete.get("outbound_events", custody_summary.get("event_count", "—"))}</div>
      <div class="kpi-sub">Transfer events in completed trace</div>
    </div>
  </div>

  <br>
  <div class="success-note">
    <b>Audit finding:</b> The primary BSC custody wallet <code>{target_wallet}</code> has been traced to zero balance.
    The largest recipients form the next custody/distribution layer and should be traced individually.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    if not custody_recipients.empty:
        show = custody_recipients.copy()

        if "amount_cell" in show.columns:
            show["amount_cell_num"] = pd.to_numeric(show["amount_cell"], errors="coerce").fillna(0)
            show = show.sort_values("amount_cell_num", ascending=False)
            show["amount_cell"] = show["amount_cell_num"].map(lambda x: f"{x:,.8f}")
            show = show.drop(columns=["amount_cell_num"], errors="ignore")

        if "share_of_total_out_percent" in show.columns:
            show["share_of_total_out_percent"] = (
                pd.to_numeric(show["share_of_total_out_percent"], errors="coerce")
                .fillna(0)
                .map(lambda x: f"{x:,.2f}%")
            )

        st.markdown("### Top Recipients from Completed 0xc3b8 Trace")
        st.dataframe(show.head(25), use_container_width=True, hide_index=True)

else:
    st.markdown(
        """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Primary BSC Custody Wallet Trace</h2>
      <p>Run <code>python3 auto_trace_bsc_wallet.py</code> to generate the completed 0xc3b8 trace.</p>
    </div>
    <div class="badge orange">Pending trace output</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ==============================
# EXPOSURE + STATUS
# ==============================

st.markdown('<a id="evidence"></a>', unsafe_allow_html=True)
e1, e2 = st.columns([1.05, .95])

total_exposure = float(route_cex) + float(route_dex) + float(route_mev)
cex_pct = float(route_cex) / total_exposure * 100 if total_exposure else 0
dex_pct = float(route_dex) / total_exposure * 100 if total_exposure else 0
mev_pct = float(route_mev) / total_exposure * 100 if total_exposure else 0

with e1:
    st.markdown(
        f"""
<div class="section">
  <div class="section-title">
    <div>
      <h2>Market Route Exposure</h2>
      <p>Route exposure identifies paths into market infrastructure. It does not equal exact realized sale volume.</p>
    </div>
    <div class="badge purple">Exposure ≠ sale amount</div>
  </div>
  <div class="exposure-row">
    <div class="exposure-card">
      <div class="exposure-head"><div class="exposure-label">Known CEX route exposure</div><div class="exposure-value">{compact(route_cex)} CELL</div></div>
      <div class="bar"><span style="width:{cex_pct:.1f}%"></span></div>
    </div>
    <div class="exposure-card">
      <div class="exposure-head"><div class="exposure-label">Known DEX / router exposure</div><div class="exposure-value">{compact(route_dex)} CELL</div></div>
      <div class="bar purple"><span style="width:{dex_pct:.1f}%"></span></div>
    </div>
    <div class="exposure-card">
      <div class="exposure-head"><div class="exposure-label">Known MEV / searcher exposure</div><div class="exposure-value">{compact(route_mev)} CELL</div></div>
      <div class="bar orange"><span style="width:{mev_pct:.1f}%"></span></div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

with e2:
    st.markdown(
        """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Evidence Status</h2>
      <p>What is verified, what is supported, and what remains open.</p>
    </div>
  </div>
  <div class="success-note">✓ Bridge infrastructure identified</div><br>
  <div class="success-note">✓ ETH and BSC supply creation verified</div><br>
  
  <div class="success-note">✓ Verified Gate.io-bound route exposure now totals at least 2,596,567.55 CELL from traced BSC supply paths</div><br>

  <div class="success-note">✓ CEX / DEX / MEV route exposure mapped</div><br>
  <div class="note">⚠ Exact realized sale proceeds remain unresolved because CEX trading is off-chain.</div><br>
  <div class="note">⚠ Full reserve/backing reconciliation remains open until all reserve and custody wallets are verified.</div>
</div>
        """,
        unsafe_allow_html=True,
    )

# ==============================
# DATA TABLES
# ==============================

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Evidence Tables</h2>
      <p>Structured evidence used by the audit site.</p>
    </div>
    <div class="badge blue">Reproducible data</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["Verified BSC supply edges", "Terminal endpoints", "Unclassified wallets"])

with tab1:
    if edges_display.empty:
        st.info("verified_bsc_supply_edges.csv not found yet.")
    else:
        show = edges_display.drop(columns=[c for c in ["_step_num"] if c in edges_display.columns], errors="ignore")
        st.dataframe(safe_df(show), use_container_width=True, hide_index=True)

with tab2:
    if terminals.empty:
        st.info("bridge_cluster_terminal_endpoints.csv not found yet.")
    else:
        show = terminals.copy()
        for c in ["terminal_inflow_possible_cell", "amount_cell", "inflow_cell"]:
            if c in show.columns:
                show[c] = pd.to_numeric(show[c], errors="coerce")
        st.dataframe(safe_df(show.head(50)), use_container_width=True, hide_index=True)

with tab3:
    if unclassified.empty:
        st.info("bridge_cluster_unclassified_wallets.csv not found yet.")
    else:
        st.dataframe(safe_df(unclassified.head(50)), use_container_width=True, hide_index=True)

# ==============================
# CHART
# ==============================

if alt is not None:
    chart_df = pd.DataFrame(
        [
            {"category": "CEX", "amount_cell": float(route_cex)},
            {"category": "DEX / Router", "amount_cell": float(route_dex)},
            {"category": "MEV / Searcher", "amount_cell": float(route_mev)},
            {"category": "Verified Gate.io Path", "amount_cell": float(gateio_verified)},
        ]
    )
    st.markdown(
        """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Exposure Comparison</h2>
      <p>High-level comparison of route exposure categories and verified BSC Gate.io path.</p>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("category:N", title=None, sort="-y"),
            y=alt.Y("amount_cell:Q", title="CELL"),
            tooltip=[
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("amount_cell:Q", title="CELL", format=",.2f"),
            ],
        )
        .properties(height=360)
    )
    st.altair_chart(chart, use_container_width=True)


# ==============================
# RESERVE / BACKING RECONCILIATION
# ==============================

reserve_recon = load_json(Path("reserve_backing_reconciliation.json"))
st.markdown('<a id="reserve-backing"></a>', unsafe_allow_html=True)
if reserve_recon:
    rt = reserve_recon.get("totals", {})
    rstatus = reserve_recon.get("status", "unresolved")
    st.markdown(
        f"""
<div class="section">
  <div class="section-title">
    <div>
      <h2>Reserve / Backing Reconciliation</h2>
      <p>This section separates contract supply from backing-eligible custody balances. CEX, DEX, router, MEV, zero, and dead addresses are excluded from backing by default.</p>
    </div>
    <div class="badge orange">Status: {rstatus}</div>
  </div>
  <div class="kpi-grid" style="grid-template-columns:repeat(4,1fr);">
    <div class="kpi-card tone-blue"><div class="kpi-label">ETH backing candidates</div><div class="kpi-value">{compact(rt.get("eth_backing_candidate_included_cell", 0))}</div><div class="kpi-sub">Current CELL held by configured ETH reserve/custody candidates</div></div>
    <div class="kpi-card tone-orange"><div class="kpi-label">BSC totalSupply</div><div class="kpi-value">{compact(rt.get("bsc_total_supply_cell", 0))}</div><div class="kpi-sub">Amount that must be explained if BSC is bridge-backed</div></div>
    <div class="kpi-card tone-red"><div class="kpi-label">BSC supply minus ETH backing</div><div class="kpi-value">{compact(rt.get("bsc_supply_minus_eth_backing_candidate_cell", 0))}</div><div class="kpi-sub">Open gap under current candidate set</div></div>
    <div class="kpi-card tone-purple"><div class="kpi-label">All backing/custody candidates</div><div class="kpi-value">{compact(rt.get("all_chain_backing_candidate_included_cell", 0))}</div><div class="kpi-sub">ETH + BSC candidates, excluding terminals</div></div>
  </div><br>
  <div class="note"><b>Audit-safe interpretation:</b> Full backing is only proven if verified reserve/custody balances and bridge accounting explain the issued cross-chain supply. If the gap remains positive, reserve/backing reconciliation remains open.</div>
</div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
<div class="section">
  <div class="section-title"><div><h2>Reserve / Backing Reconciliation</h2><p>Run <code>python3 reserve_backing_reconciliation.py</code> to generate the current reserve/backing reconciliation.</p></div><div class="badge orange">Open</div></div>
  <div class="note">Full reserve/backing reconciliation remains open until all reserve and custody wallets are verified.</div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ==============================
# DOWNLOADS
# ==============================

st.markdown('<a id="downloads"></a>', unsafe_allow_html=True)
st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Downloads & Resources</h2>
      <p>Download the evidence package used by this one-page audit site.</p>
    </div>
    <div class="badge">Evidence package</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

dcols = st.columns(4)
with dcols[0]:
    download_if_exists("Verified supply findings JSON", VERIFIED_FINDINGS, "application/json")
    download_if_exists("Total supply snapshot JSON", TOTAL_SUPPLY, "application/json")
with dcols[1]:
    download_if_exists("Verified BSC supply edges CSV", VERIFIED_EDGES, "text/csv")
    download_if_exists("Supply events summary JSON", SUPPLY_EVENTS, "application/json")
with dcols[2]:
    download_if_exists("Bridge cluster summary JSON", BRIDGE_CLUSTER, "application/json")
    download_if_exists("Terminal endpoints CSV", TERMINALS, "text/csv")
with dcols[3]:
    download_if_exists("Evidence notes Markdown", EVIDENCE_NOTES, "text/markdown")
    download_if_exists("Wallet label priority CSV", WALLET_PRIORITY, "text/csv")

st.markdown(
    """
<div class="footer">
  <div class="footer-item"><b>100% On-chain</b>Every core finding is tied to blockchain-visible data or exported evidence files.</div>
  <div class="footer-item"><b>Reproducible</b>Scripts and CSV/JSON outputs allow the audit to be rerun and checked independently.</div>
  <div class="footer-item"><b>Tamper-resistant</b>Transaction hashes and explorer links anchor the findings to public ledgers.</div>
  <div class="footer-item"><b>Audit caveat</b>Route exposure is not exact realized sale amount; reserve backing remains a separate open question.</div>
</div>
""",
    unsafe_allow_html=True,
)
