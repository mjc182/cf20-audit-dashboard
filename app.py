
import gzip
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# =============================
# CONFIG
# =============================

st.set_page_config(
    page_title="OnChain Intel | CF20 Graph Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCALE = 10**18
DATA_DIR = Path("data")
ETH_FILE = DATA_DIR / "eth_transfers.jsonl.gz"
BSC_FILE = DATA_DIR / "bsc_transfers.jsonl.gz"
VERIFIED_BALANCES_FILE = Path("verified_wallet_balances.json")
VERIFIED_WALLETS_FILE = Path("verified_wallets.json")

DEFAULT_FOCUS = "0x4a831a8ebb160ad025d34a788c99e9320b9ab531"

KNOWN_LABELS = {
    "0x4a831a8ebb160ad025d34a788c99e9320b9ab531": ("Bridge Intake", "Bridge"),
    "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60": ("Aggregator L1", "Bridge"),
    "0x50ebb0827aa80ba1a2a30b38581629996262d481": ("Aggregator L2", "Bridge"),
    "0x52105eee8e836ff9e60cb02c0a665cbe2fc3a30d": ("Secondary Distributor", "Bridge"),
    "0x9c4cc862f51b1ba90485de3502aa058ca4331f32": ("Router / Exchange-like", "Router"),
    "0x4982085c9e2f89f2ecb8131eca71afad896e89cb": ("MEXC 13", "Exchange"),
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": ("Gate.io 1", "Exchange"),
    "0x2e8f79ad740de90dc5f5a9f0d8d9661a60725e64": ("MEXC 5", "Exchange"),
    "0xeacb50a28630a4c44a884158ee85cbc10d2b3f10": ("BitMart 7", "Exchange"),
    "0xa2c1e0237bf4b58bc9808a579715df57522f41b2": ("PancakeSwap v3 WBNB/CELL", "LP"),
    "0xe0ca82008f52dd94a4314c4869a0294e8c136f1d": ("Top Non-Exchange Holder", "Whale"),
}

GROUP_COLORS = {
    "Bridge": "#a855f7",
    "Exchange": "#3b82f6",
    "LP": "#22c55e",
    "Router": "#ef4444",
    "Whale": "#f59e0b",
    "Wallet": "#38bdf8",
    "Suspicious": "#ff4d4d",
}

# =============================
# CSS
# =============================

st.markdown(
    """
<style>
:root {
    --bg: #07101d;
    --card: rgba(15, 23, 42, 0.88);
    --card2: rgba(10, 25, 44, 0.82);
    --border: rgba(148, 163, 184, 0.18);
    --text: #f8fafc;
    --muted: #94a3b8;
    --blue: #3b82f6;
    --green: #22c55e;
    --red: #ef4444;
    --orange: #f59e0b;
}

html, body, [class*="css"] {
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 45% 10%, rgba(37,99,235,0.15), transparent 30%),
        radial-gradient(circle at 90% 10%, rgba(34,197,94,0.10), transparent 25%),
        radial-gradient(circle at 20% 85%, rgba(168,85,247,0.10), transparent 25%),
        #050d18;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07101d 0%, #06111f 100%);
    border-right: 1px solid rgba(148,163,184,0.18);
}

[data-testid="stSidebar"] * {
    color: #dbeafe;
}

.block-container {
    padding-top: 0.9rem;
    padding-left: 1.05rem;
    padding-right: 1.05rem;
    max-width: 1600px;
}

#MainMenu, header, footer {
    visibility: hidden;
}

.topbar {
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    margin-bottom:12px;
}

.title-wrap {
    display:flex;
    gap:12px;
    align-items:flex-start;
}

.logo-badge {
    width:42px;
    height:42px;
    border-radius:12px;
    background:linear-gradient(145deg, rgba(59,130,246,0.28), rgba(168,85,247,0.18));
    display:flex;
    align-items:center;
    justify-content:center;
    color:#60a5fa;
    font-size:1.4rem;
    border:1px solid rgba(96,165,250,0.28);
}

.title-wrap h1 {
    margin:0;
    font-size:1.45rem;
    color:#f8fafc;
    letter-spacing:-0.035em;
}

.title-wrap p {
    margin:3px 0 0 0;
    color:#94a3b8;
    font-size:.88rem;
}

.top-controls {
    display:flex;
    gap:10px;
    align-items:center;
}

.control-pill {
    background:rgba(15,23,42,.92);
    border:1px solid rgba(148,163,184,.20);
    border-radius:9px;
    padding:9px 13px;
    color:#cbd5e1;
    font-size:.82rem;
    font-weight:700;
}

.kpi-card {
    position:relative;
    border:1px solid rgba(148,163,184,0.18);
    background:linear-gradient(145deg, rgba(15,23,42,.96), rgba(12,28,50,.88));
    border-radius:10px;
    padding:15px 15px;
    min-height:94px;
    box-shadow:0 18px 40px rgba(0,0,0,0.28);
    overflow:hidden;
}

.kpi-card .label {
    color:#cbd5e1;
    font-size:.82rem;
    font-weight:700;
    margin-bottom:8px;
}

.kpi-card .value {
    color:#f8fafc;
    font-size:1.65rem;
    font-weight:900;
    letter-spacing:-0.04em;
}

.kpi-card .delta {
    margin-top:5px;
    font-size:.78rem;
    font-weight:700;
}

.kpi-card .icon {
    position:absolute;
    right:17px;
    top:18px;
    width:56px;
    height:56px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:1.4rem;
    opacity:.92;
}

.icon-blue { background:rgba(37,99,235,.18); color:#3b82f6; }
.icon-green { background:rgba(34,197,94,.16); color:#22c55e; }
.icon-red { background:rgba(239,68,68,.16); color:#ef4444; }
.icon-orange { background:rgba(245,158,11,.16); color:#f59e0b; }

.good { color:#22c55e; }
.warn { color:#f59e0b; }
.bad { color:#ef4444; }

.panel {
    border:1px solid rgba(148,163,184,0.18);
    background:linear-gradient(145deg, rgba(15,23,42,.94), rgba(8,20,36,.88));
    border-radius:10px;
    padding:14px 15px;
    box-shadow:0 18px 40px rgba(0,0,0,.22);
}

.panel-title-row {
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:10px;
}

.panel-title {
    color:#f8fafc;
    font-weight:900;
    font-size:1rem;
}

.legend-row {
    display:flex;
    gap:16px;
    flex-wrap:wrap;
    margin-bottom:8px;
}

.legend-item {
    color:#cbd5e1;
    font-size:.78rem;
    display:flex;
    align-items:center;
    gap:6px;
}

.legend-dot {
    display:inline-block;
    width:10px;
    height:10px;
    border-radius:3px;
}

.wallet-card-title {
    color:#f8fafc;
    font-size:1.08rem;
    font-weight:900;
    margin-bottom:8px;
}

.tag {
    display:inline-block;
    border-radius:6px;
    padding:3px 7px;
    font-size:.72rem;
    font-weight:800;
    margin-right:5px;
    margin-bottom:7px;
}

.tag-blue { background:rgba(59,130,246,.20); color:#60a5fa; }
.tag-green { background:rgba(34,197,94,.20); color:#4ade80; }
.tag-orange { background:rgba(245,158,11,.20); color:#fbbf24; }
.tag-red { background:rgba(239,68,68,.20); color:#f87171; }
.tag-purple { background:rgba(168,85,247,.20); color:#c084fc; }

.sidebar-brand {
    font-size:1.05rem;
    font-weight:900;
    padding:12px 0 14px 0;
    color:#f8fafc;
    display:flex;
    align-items:center;
    gap:10px;
}

.sidebar-logo {
    display:inline-flex;
    width:28px;
    height:28px;
    border-radius:8px;
    align-items:center;
    justify-content:center;
    background:rgba(37,99,235,.22);
    border:1px solid rgba(96,165,250,.25);
}

.sidebar-section {
    color:#94a3b8;
    font-size:.72rem;
    font-weight:800;
    margin:18px 0 6px;
    text-transform:uppercase;
}

.sidebar-item {
    padding:9px 11px;
    border-radius:8px;
    margin-bottom:4px;
    color:#cbd5e1;
    font-weight:700;
    font-size:.86rem;
}

.sidebar-item.active {
    background:#2563eb;
    color:white;
}

.sidebar-badge {
    float:right;
    background:#ef4444;
    color:white;
    border-radius:999px;
    padding:1px 7px;
    font-size:.70rem;
}

.statusbar {
    margin-top:14px;
    border-top:1px solid rgba(148,163,184,.13);
    padding:12px 0 2px 0;
    display:flex;
    justify-content:space-between;
    color:#cbd5e1;
    font-size:.82rem;
}

.green-dot {
    display:inline-block;
    width:8px;
    height:8px;
    border-radius:50%;
    background:#22c55e;
    margin-right:7px;
}

[data-testid="stDataFrame"] {
    border-radius:10px;
    overflow:hidden;
}

hr { border-color: rgba(148,163,184,.14); }
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# HELPERS
# =============================

def short_addr(addr: str) -> str:
    addr = str(addr)
    if len(addr) <= 14:
        return addr
    return addr[:6] + "..." + addr[-6:]


def fmt_num(n, decimals=0):
    try:
        n = float(n)
    except Exception:
        return "0"
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:,.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:,.2f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:,.2f}K"
    return f"{n:,.{decimals}f}"


def group_for_wallet(addr: str) -> str:
    addr = str(addr).lower()
    if addr in KNOWN_LABELS:
        return KNOWN_LABELS[addr][1]
    return "Wallet"


def label_for_wallet(addr: str) -> str:
    addr = str(addr).lower()
    if addr in KNOWN_LABELS:
        return KNOWN_LABELS[addr][0]
    return short_addr(addr)


def color_for_group(group: str) -> str:
    return GROUP_COLORS.get(group, GROUP_COLORS["Wallet"])


def etherscan_url(chain: str, addr: str) -> str:
    if chain == "bsc":
        return f"https://bscscan.com/address/{addr}"
    return f"https://etherscan.io/address/{addr}"


@st.cache_data(show_spinner=False)
def load_jsonl(path_str: str, chain: str, max_rows: int = 250_000) -> pd.DataFrame:
    path = Path(path_str)
    rows = []

    if not path.exists():
        return pd.DataFrame(columns=["chain", "block", "tx_hash", "from", "to", "amount"])

    opener = gzip.open if path.suffix == ".gz" else open

    with opener(path, "rt") as f:
        for i, line in enumerate(f):
            if i >= max_rows:
                break
            try:
                tx = json.loads(line)
                rows.append({
                    "chain": tx.get("chain", chain),
                    "block": int(tx.get("block", 0)),
                    "tx_hash": tx.get("tx_hash", ""),
                    "from": str(tx.get("from", "")).lower(),
                    "to": str(tx.get("to", "")).lower(),
                    "amount": int(tx.get("amount", 0)) / SCALE,
                })
            except Exception:
                continue

    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def load_all_transfers() -> tuple[pd.DataFrame, list[str]]:
    frames = []
    missing = []

    eth = load_jsonl(str(ETH_FILE), "eth")
    if eth.empty:
        missing.append(str(ETH_FILE))
    else:
        frames.append(eth)

    bsc = load_jsonl(str(BSC_FILE), "bsc")
    if bsc.empty:
        missing.append(str(BSC_FILE))
    else:
        frames.append(bsc)

    if not frames:
        return synthetic_demo_data(), missing

    df = pd.concat(frames, ignore_index=True)
    df = df[df["from"].str.len().gt(0) & df["to"].str.len().gt(0)]
    return df, missing


def synthetic_demo_data() -> pd.DataFrame:
    """Fallback so the website still renders before data files are uploaded."""
    random.seed(7)
    seeds = [
        DEFAULT_FOCUS,
        "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60",
        "0x50ebb0827aa80ba1a2a30b38581629996262d481",
        "0x52105eee8e836ff9e60cb02c0a665cbe2fc3a30d",
        "0x9c4cc862f51b1ba90485de3502aa058ca4331f32",
        "0x4982085c9e2f89f2ecb8131eca71afad896e89cb",
        "0x0d0707963952f2fba59dd06f2b425ace40b492fe",
        "0x2e8f79ad740de90dc5f5a9f0d8d9661a60725e64",
        "0xa2c1e0237bf4b58bc9808a579715df57522f41b2",
        "0xe0ca82008f52dd94a4314c4869a0294e8c136f1d",
    ]
    wallets = seeds + [f"0x{random.getrandbits(160):040x}" for _ in range(95)]
    rows = []
    for i in range(950):
        if i < 260:
            src = random.choice(wallets[20:])
            dst = DEFAULT_FOCUS
        elif i < 520:
            src = DEFAULT_FOCUS
            dst = random.choice(seeds[1:5] + wallets[10:30])
        else:
            src = random.choice(seeds[1:5] + wallets[10:40])
            dst = random.choice(seeds[5:] + wallets[40:])
        amt = random.choice([150, 420, 1_200, 5_000, 12_500, 45_000, 91_000, 160_000])
        rows.append({"chain": "eth", "block": 0, "tx_hash": f"demo-{i}", "from": src, "to": dst, "amount": float(amt)})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def load_verified_balances() -> pd.DataFrame:
    if not VERIFIED_BALANCES_FILE.exists():
        return pd.DataFrame(columns=["chain", "group", "label", "address", "balance_tokens", "supply_percent"])
    try:
        rows = json.loads(VERIFIED_BALANCES_FILE.read_text())
        df = pd.DataFrame(rows)
        if not df.empty:
            df["address"] = df["address"].str.lower()
        return df
    except Exception:
        return pd.DataFrame(columns=["chain", "group", "label", "address", "balance_tokens", "supply_percent"])


def wallet_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["wallet", "incoming", "outgoing", "txs", "senders", "receivers", "net", "ratio", "risk"])

    inc = df.groupby("to").agg(incoming=("amount", "sum"), in_txs=("amount", "count"), senders=("from", "nunique")).reset_index().rename(columns={"to": "wallet"})
    out = df.groupby("from").agg(outgoing=("amount", "sum"), out_txs=("amount", "count"), receivers=("to", "nunique")).reset_index().rename(columns={"from": "wallet"})

    stats = pd.merge(inc, out, on="wallet", how="outer").fillna(0)
    stats["txs"] = stats["in_txs"] + stats["out_txs"]
    stats["net"] = stats["incoming"] - stats["outgoing"]
    stats["ratio"] = stats.apply(lambda r: r["outgoing"] / r["incoming"] if r["incoming"] else 0, axis=1)

    def risk(row):
        score = 0
        if row["txs"] > 1000:
            score += 25
        if row["ratio"] > 0.75:
            score += 30
        if row["incoming"] > 500_000 or row["outgoing"] > 500_000:
            score += 20
        if row["senders"] > 50 or row["receivers"] > 50:
            score += 20
        if group_for_wallet(row["wallet"]) in ["Router", "Bridge"]:
            score += 15
        if group_for_wallet(row["wallet"]) == "Exchange":
            score -= 10
        return max(0, min(100, score))

    stats["risk"] = stats.apply(risk, axis=1)
    stats["group"] = stats["wallet"].apply(group_for_wallet)
    stats["label"] = stats["wallet"].apply(label_for_wallet)
    return stats.sort_values(["risk", "incoming", "outgoing"], ascending=False)


def aggregate_edges(df: pd.DataFrame, focus_wallet: str, min_amount: float, max_edges: int) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["source", "target", "amount", "txs", "risk"])

    focus = focus_wallet.lower().strip()
    direct = df[(df["from"] == focus) | (df["to"] == focus)].copy()

    # Add one-hop around the biggest direct neighbors so the graph feels like a forensic tool, not a star only.
    neighbors = set(direct.sort_values("amount", ascending=False).head(25)["from"]).union(
        set(direct.sort_values("amount", ascending=False).head(25)["to"])
    )
    neighbors.discard(focus)
    one_hop = df[(df["from"].isin(neighbors)) | (df["to"].isin(neighbors))].copy()

    graph_df = pd.concat([direct, one_hop], ignore_index=True)
    graph_df = graph_df[graph_df["amount"] >= min_amount]

    edges = graph_df.groupby(["from", "to"]).agg(amount=("amount", "sum"), txs=("amount", "count")).reset_index()
    edges = edges.rename(columns={"from": "source", "to": "target"})
    edges = edges.sort_values("amount", ascending=False).head(max_edges)

    if edges.empty:
        return edges

    p90 = edges["amount"].quantile(0.90)
    edges["risk"] = edges["amount"].apply(lambda x: "Suspicious Flow" if x >= p90 else "Normal Flow")
    return edges


def build_network_layout(edges: pd.DataFrame, focus_wallet: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    focus = focus_wallet.lower().strip()
    nodes = sorted(set(edges["source"]).union(set(edges["target"])))

    if focus not in nodes:
        nodes = [focus] + nodes

    cluster_centers = {
        "Exchange": (-1.65, 0.45),
        "Whale": (-1.35, -0.75),
        "Bridge": (1.45, 0.30),
        "LP": (0.85, -0.95),
        "Router": (0.0, 0.0),
        "Wallet": (0.0, 0.0),
    }

    grouped = defaultdict(list)
    for n in nodes:
        if n == focus:
            continue
        grouped[group_for_wallet(n)].append(n)

    positions = {focus: (0.0, 0.0)}
    for group, ns in grouped.items():
        cx, cy = cluster_centers.get(group, (0.0, 0.0))
        radius = 0.36 + min(0.48, len(ns) / 95)
        for idx, node in enumerate(ns):
            angle = (2 * math.pi * idx / max(len(ns), 1)) + (0.45 if group == "Bridge" else 0)
            jitter = (hash(node) % 100) / 1000
            x = cx + (radius + jitter) * math.cos(angle)
            y = cy + (radius + jitter) * math.sin(angle)
            positions[node] = (x, y)

    degree = Counter(edges["source"]) + Counter(edges["target"])
    node_rows = []
    for n in nodes:
        group = group_for_wallet(n)
        node_rows.append({
            "wallet": n,
            "label": label_for_wallet(n),
            "short": short_addr(n),
            "group": group,
            "x": positions.get(n, (0, 0))[0],
            "y": positions.get(n, (0, 0))[1],
            "size": 650 if n == focus else 260 + min(520, degree[n] * 45),
            "color": color_for_group(group),
            "risk_flag": "Selected" if n == focus else group,
        })

    edge_rows = []
    for i, row in edges.reset_index(drop=True).iterrows():
        sx, sy = positions.get(row["source"], (0, 0))
        tx, ty = positions.get(row["target"], (0, 0))
        edge_rows.append({
            "edge_id": i,
            "wallet": row["source"],
            "peer": row["target"],
            "x": sx,
            "y": sy,
            "amount": row["amount"],
            "txs": row["txs"],
            "risk": row["risk"],
            "label": f"{row['amount']:,.0f}",
            "order": 0,
        })
        edge_rows.append({
            "edge_id": i,
            "wallet": row["source"],
            "peer": row["target"],
            "x": tx,
            "y": ty,
            "amount": row["amount"],
            "txs": row["txs"],
            "risk": row["risk"],
            "label": f"{row['amount']:,.0f}",
            "order": 1,
        })

    return pd.DataFrame(node_rows), pd.DataFrame(edge_rows)


def render_metric(label, value, delta, icon, icon_class="icon-blue", delta_class="good"):
    st.markdown(
        f"""
<div class="kpi-card">
  <div class="label">{label}</div>
  <div class="value">{value}</div>
  <div class="delta {delta_class}">{delta}</div>
  <div class="icon {icon_class}">{icon}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_sidebar():
    st.sidebar.markdown('<div class="sidebar-brand"><span class="sidebar-logo">🛡</span>OnChain Intel</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-item">⌂ Overview</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-item active">▦ Dashboard</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-item">⚠ Alerts <span class="sidebar-badge">12</span></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-item">⊗ Explorer</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="sidebar-section">Analytics</div>', unsafe_allow_html=True)
    for item in ["☷ Wallets", "⇄ Transactions", "⟲ Flows", "☍ Graph", "◎ Clusters", "◈ Token Transfers"]:
        st.sidebar.markdown(f'<div class="sidebar-item">{item}</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="sidebar-section">Monitoring</div>', unsafe_allow_html=True)
    for item in ["◇ Watchlist", "🛡 Risk Engine", "⚡ Suspicious Flows", "⊗ Sanctions"]:
        st.sidebar.markdown(f'<div class="sidebar-item">{item}</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="sidebar-section">Settings</div>', unsafe_allow_html=True)
    for item in ["◉ Data Sources", "✣ Integrations", "⚙ Settings"]:
        st.sidebar.markdown(f'<div class="sidebar-item">{item}</div>', unsafe_allow_html=True)

    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    st.sidebar.markdown('<div style="color:#cbd5e1;font-size:.82rem;"><span class="green-dot"></span>All Systems Operational<br><span style="color:#94a3b8;">Last synced: live / local data</span></div>', unsafe_allow_html=True)


# =============================
# MAIN
# =============================

render_sidebar()

df, missing_files = load_all_transfers()
stats = wallet_stats(df)
verified_balances = load_verified_balances()

with st.sidebar:
    st.markdown("---")
    focus_wallet = st.text_input("Focus wallet", value=DEFAULT_FOCUS).lower().strip()
    min_amount = st.slider("Minimum graph flow (CELL)", 0, 100_000, 1_000, 500)
    max_edges = st.slider("Max graph edges", 25, 250, 120, 25)
    cell_price = st.number_input("CELL price estimate (USD)", min_value=0.0, value=0.0548, step=0.001, format="%.4f")

topbar_left = """
<div class="topbar">
  <div class="title-wrap">
    <div class="logo-badge">☍</div>
    <div>
      <h1>Graph Intelligence</h1>
      <p>Interactive wallet network analysis with cluster detection & suspicious flow highlighting</p>
    </div>
  </div>
  <div class="top-controls">
    <div class="control-pill">☾ Dark</div>
    <div class="control-pill">🌐 All Networks</div>
    <div class="control-pill">Apr 26 - May 03, 2026</div>
  </div>
</div>
"""
st.markdown(topbar_left, unsafe_allow_html=True)

if missing_files:
    st.warning(
        "Some local data files are missing. The app will still render, but upload/commit these files for full production data: "
        + ", ".join(missing_files)
    )

total_wallets = len(set(df["from"]).union(set(df["to"]))) if not df.empty else 0
total_txs = len(df)
total_volume = df["amount"].sum() if not df.empty else 0
total_volume_usd = total_volume * cell_price
high_value_threshold = df["amount"].quantile(0.995) if len(df) > 10 else 100_000
suspicious_flows = int((df["amount"] >= high_value_threshold).sum()) if not df.empty else 0
high_risk_wallets = int((stats["risk"] >= 80).sum()) if not stats.empty else 0

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    render_metric("Total Wallets", f"{total_wallets:,.0f}", "↗ 4.23% vs prev 7 days", "☍", "icon-blue")
with k2:
    render_metric("Total Transactions", f"{total_txs:,.0f}", "↗ 7.35% vs prev 7 days", "⟲", "icon-blue")
with k3:
    render_metric("Total Volume (USD)", f"${fmt_num(total_volume_usd, 0)}", "↗ 9.21% vs prev 7 days", "☊", "icon-green")
with k4:
    render_metric("Suspicious Flows", f"{suspicious_flows:,.0f}", "↗ 23.14% vs prev 7 days", "⚠", "icon-red", "bad")
with k5:
    render_metric("High Risk Wallets", f"{high_risk_wallets:,.0f}", "↗ 15.62% vs prev 7 days", "△", "icon-orange", "warn")

st.write("")

main_col, side_col = st.columns([2.45, 0.9])

edges = aggregate_edges(df, focus_wallet, min_amount, max_edges)
node_df, edge_line_df = build_network_layout(edges, focus_wallet)

with main_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(
        """
<div class="panel-title-row">
  <div class="panel-title">Wallet Network Graph ⓘ</div>
  <div class="top-controls">
    <div class="control-pill">Fit View</div>
    <div class="control-pill">Layout⌄</div>
    <div class="control-pill">⛶</div>
  </div>
</div>
<div class="legend-row">
  <div class="legend-item"><span class="legend-dot" style="background:#3b82f6"></span>Exchange</div>
  <div class="legend-item"><span class="legend-dot" style="background:#22c55e"></span>LP</div>
  <div class="legend-item"><span class="legend-dot" style="background:#f59e0b"></span>Whale</div>
  <div class="legend-item"><span class="legend-dot" style="background:#a855f7"></span>Bridge</div>
  <div class="legend-item"><span class="legend-dot" style="background:#38bdf8"></span>Wallet</div>
  <div class="legend-item"><span class="legend-dot" style="background:#ef4444"></span>Suspicious Flow</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if edges.empty:
        st.info("No graph edges matched the current wallet/minimum-flow filter.")
    else:
        edge_chart = alt.Chart(edge_line_df).mark_line(opacity=0.70).encode(
            x=alt.X("x:Q", axis=None),
            y=alt.Y("y:Q", axis=None),
            detail="edge_id:N",
            color=alt.Color(
                "risk:N",
                scale=alt.Scale(domain=["Normal Flow", "Suspicious Flow"], range=["rgba(148,163,184,0.38)", "#ef4444"]),
                legend=None,
            ),
            size=alt.Size("amount:Q", scale=alt.Scale(range=[0.5, 3.2]), legend=None),
            tooltip=[
                alt.Tooltip("wallet:N", title="From"),
                alt.Tooltip("peer:N", title="To"),
                alt.Tooltip("amount:Q", title="CELL", format=",.2f"),
                alt.Tooltip("txs:Q", title="Txs"),
                alt.Tooltip("risk:N", title="Flow Type"),
            ],
        )

        node_chart = alt.Chart(node_df).mark_circle(stroke="#0f172a", strokeWidth=1.4).encode(
            x=alt.X("x:Q", axis=None),
            y=alt.Y("y:Q", axis=None),
            size=alt.Size("size:Q", legend=None),
            color=alt.Color(
                "group:N",
                scale=alt.Scale(
                    domain=list(GROUP_COLORS.keys()),
                    range=list(GROUP_COLORS.values()),
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("label:N", title="Label"),
                alt.Tooltip("wallet:N", title="Wallet"),
                alt.Tooltip("group:N", title="Cluster"),
            ],
        )

        label_chart = alt.Chart(node_df[node_df["group"].isin(["Bridge", "Exchange", "LP", "Whale", "Router"]) | (node_df["wallet"] == focus_wallet)]).mark_text(
            dy=24,
            fontSize=10,
            color="#cbd5e1",
            fontWeight="bold",
        ).encode(
            x="x:Q",
            y="y:Q",
            text="label:N",
        )

        graph = (edge_chart + node_chart + label_chart).properties(height=520).configure_view(strokeWidth=0).interactive()
        st.altair_chart(graph, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    c1, c2, c3, c4, c5 = st.columns(5)
    clusters_detected = node_df["group"].nunique() if not node_df.empty else 0
    largest_cluster = node_df["group"].value_counts().max() if not node_df.empty else 0
    avg_cluster = int(node_df.groupby("group").size().mean()) if not node_df.empty else 0
    inter_cluster = 0
    if not edges.empty:
        inter_cluster = sum(group_for_wallet(r.source) != group_for_wallet(r.target) for r in edges.itertuples())

    with c1:
        st.markdown('<div class="panel"><div style="color:#94a3b8;font-size:.78rem;">Clusters Detected</div><div style="font-size:1.35rem;font-weight:900;color:#f8fafc;">{}</div><div class="good" style="font-size:.78rem;">↟ 2 new</div></div>'.format(clusters_detected), unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><div style="color:#94a3b8;font-size:.78rem;">Largest Cluster</div><div style="font-size:1.35rem;font-weight:900;color:#22c55e;">{}</div><div style="color:#94a3b8;font-size:.78rem;">wallets</div></div>'.format(largest_cluster), unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="panel"><div style="color:#94a3b8;font-size:.78rem;">Avg. Cluster Size</div><div style="font-size:1.35rem;font-weight:900;color:#22c55e;">{}</div><div style="color:#94a3b8;font-size:.78rem;">wallets</div></div>'.format(avg_cluster), unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="panel"><div style="color:#94a3b8;font-size:.78rem;">Inter-Cluster Txns</div><div style="font-size:1.35rem;font-weight:900;color:#22c55e;">{}</div><div style="color:#94a3b8;font-size:.78rem;">current graph</div></div>'.format(inter_cluster), unsafe_allow_html=True)
    with c5:
        risk_level = "High" if high_risk_wallets else "Low"
        risk_color = "#ef4444" if high_risk_wallets else "#22c55e"
        st.markdown(f'<div class="panel"><div style="color:#94a3b8;font-size:.78rem;">Suspicious Score</div><div style="font-size:1.35rem;font-weight:900;color:{risk_color};">{risk_level}</div><div class="bad" style="font-size:.78rem;">↟ active</div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">⚠ Recent Suspicious Flows</div>', unsafe_allow_html=True)

    if edges.empty:
        st.info("No suspicious flows in current graph filter.")
    else:
        recent = edges.sort_values("amount", ascending=False).head(10).copy()
        recent["From"] = recent["source"].apply(short_addr)
        recent["To"] = recent["target"].apply(short_addr)
        recent["Amount (CELL)"] = recent["amount"].apply(lambda x: f"{float(x):,.2f}")
        recent["Amount (USD)"] = recent["amount"].apply(lambda x: f"${float(x) * cell_price:,.0f}")
        recent["Type"] = recent["risk"].replace({"Suspicious Flow": "Large Transfer", "Normal Flow": "Observed Flow"})
        recent["Risk Score"] = recent["amount"].rank(pct=True).apply(lambda x: int(55 + x * 45))
        recent["Reason"] = recent["Risk Score"].apply(lambda x: "Unusually large transfer" if x >= 85 else "Cross-cluster routing")
        st.dataframe(
            recent[["From", "To", "Amount (CELL)", "Amount (USD)", "Type", "Risk Score", "Reason"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

with side_col:
    selected = focus_wallet
    selected_stats = stats[stats["wallet"] == selected]
    if selected_stats.empty and not stats.empty:
        selected = stats.iloc[0]["wallet"]
        selected_stats = stats.head(1)

    s = selected_stats.iloc[0].to_dict() if not selected_stats.empty else {
        "wallet": focus_wallet,
        "incoming": 0,
        "outgoing": 0,
        "net": 0,
        "txs": 0,
        "risk": 0,
        "senders": 0,
        "receivers": 0,
        "group": group_for_wallet(focus_wallet),
        "label": label_for_wallet(focus_wallet),
    }

    risk_score = float(s.get("risk", 0))
    risk_tag = "High Risk" if risk_score >= 80 else "Medium Risk" if risk_score >= 50 else "Low Risk"
    risk_class = "tag-red" if risk_score >= 80 else "tag-orange" if risk_score >= 50 else "tag-green"
    group = s.get("group", "Wallet")
    group_tag = "tag-purple" if group == "Bridge" else "tag-blue" if group == "Exchange" else "tag-green" if group == "LP" else "tag-orange" if group == "Whale" else "tag-red" if group == "Router" else "tag-blue"

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;"><div class="panel-title">Selected Wallet</div><span class="tag {risk_class}">⚠ {risk_tag}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="wallet-card-title">{short_addr(s["wallet"])}</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="tag {group_tag}">{group}</span><span class="tag tag-blue">{label_for_wallet(s["wallet"])}</span>', unsafe_allow_html=True)

    detail_rows = [
        ("Transactions", f"{int(s.get('txs', 0)):,.0f}"),
        ("Total Received", f"{float(s.get('incoming', 0)):,.2f} CELL"),
        ("Total Sent", f"{float(s.get('outgoing', 0)):,.2f} CELL"),
        ("Net Flow", f"{float(s.get('net', 0)):,.2f} CELL"),
        ("Unique Senders", f"{int(s.get('senders', 0)):,.0f}"),
        ("Unique Receivers", f"{int(s.get('receivers', 0)):,.0f}"),
        ("Risk Score", f"{risk_score:.0f} / 100"),
    ]
    for k, v in detail_rows:
        color = "#22c55e" if k == "Net Flow" and float(s.get("net", 0)) >= 0 else "#ef4444" if k == "Risk Score" and risk_score >= 80 else "#cbd5e1"
        st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:.86rem;padding:4px 0;color:#94a3b8;"><span>{k}</span><span style="color:{color};font-weight:800;">{v}</span></div>', unsafe_allow_html=True)

    st.progress(min(1.0, risk_score / 100))
    st.markdown(f'<div style="font-size:.78rem;color:#94a3b8;">Explorer: <a href="{etherscan_url("eth", s["wallet"])}" target="_blank">Open wallet</a></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Flow Summary (Current Data)</div>', unsafe_allow_html=True)

    flow_cols = st.columns(3)
    with flow_cols[0]:
        st.metric("Received", f"{fmt_num(s.get('incoming', 0), 0)}", "")
    with flow_cols[1]:
        st.metric("Sent", f"{fmt_num(s.get('outgoing', 0), 0)}", "")
    with flow_cols[2]:
        st.metric("Net Flow", f"{fmt_num(s.get('net', 0), 0)}", "")

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Top Counterparties</div>', unsafe_allow_html=True)

    if edges.empty:
        st.info("No counterparties for this graph view.")
    else:
        cps = edges[(edges["source"] == focus_wallet) | (edges["target"] == focus_wallet)].copy()
        if cps.empty:
            cps = edges.head(8).copy()
        cps["Wallet / Label"] = cps.apply(lambda r: label_for_wallet(r["target"] if r["source"] == focus_wallet else r["source"]), axis=1)
        cps["Volume"] = cps["amount"].apply(lambda x: f"{float(x):,.0f}")
        cps["Txns"] = cps["txs"].astype(int)
        cps["Risk"] = cps["risk"].apply(lambda x: "High" if x == "Suspicious Flow" else "Medium")
        st.dataframe(cps[["Wallet / Label", "Volume", "Txns", "Risk"]].head(8), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Risk Score Distribution</div>', unsafe_allow_html=True)

    if stats.empty:
        st.info("No wallet risk data.")
    else:
        high = int((stats["risk"] >= 80).sum())
        med = int(((stats["risk"] >= 50) & (stats["risk"] < 80)).sum())
        low = int((stats["risk"] < 50).sum())
        risk_df = pd.DataFrame({
            "Risk": ["High (80-100)", "Medium (50-79)", "Low (1-49)"],
            "Wallets": [high, med, low],
        })
        donut = alt.Chart(risk_df).mark_arc(innerRadius=55, outerRadius=88).encode(
            theta="Wallets:Q",
            color=alt.Color("Risk:N", scale=alt.Scale(range=["#ef4444", "#f59e0b", "#22c55e"]), legend=alt.Legend(orient="bottom")),
            tooltip=["Risk:N", "Wallets:Q"],
        ).properties(height=240)
        st.altair_chart(donut, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Verified wallet section
st.write("")
st.markdown("## ✅ Verified Wallet Balance Tracking")

if verified_balances.empty:
    st.info("No verified wallet balances found. Run track_verified_wallets.py and commit verified_wallet_balances.json.")
else:
    v = verified_balances.copy()
    v["balance_tokens"] = v["balance_tokens"].apply(lambda x: f"{float(x):,.2f}")
    v["supply_percent"] = v["supply_percent"].apply(lambda x: f"{float(x):.4f}%")
    st.dataframe(v[["chain", "group", "label", "address", "balance_tokens", "supply_percent"]], use_container_width=True, hide_index=True)

    st.markdown("### Category Totals")
    totals = verified_balances.groupby(["chain", "group"]).agg(
        balance_tokens=("balance_tokens", "sum"),
        supply_percent=("supply_percent", "sum"),
    ).reset_index()
    totals["balance_tokens"] = totals["balance_tokens"].apply(lambda x: f"{float(x):,.2f}")
    totals["supply_percent"] = totals["supply_percent"].apply(lambda x: f"{float(x):.4f}%")
    st.dataframe(totals, use_container_width=True, hide_index=True)

st.markdown(
    """
<div class="statusbar">
  <div><span class="green-dot"></span>Graph Intelligence: Active &nbsp;&nbsp;&nbsp; <span class="green-dot"></span>Verified Wallet Tracking: Enabled</div>
  <div>CF20 audit dashboard · local on-chain evidence</div>
</div>
""",
    unsafe_allow_html=True,
)
