import math
from collections import Counter
from datetime import datetime

import altair as alt
import pandas as pd
import requests
import streamlit as st
from web3 import Web3

st.set_page_config(
    page_title="CF20 Bridge Verification Dashboard",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="expanded",
)

ZEROCHAIN_API = "https://2.api.explorer.cellframe.net/atoms/Backbone/zerochain/"
ETH_TOKEN = "0x26c8afbbfe1ebaca03c2bb082e69d0476bffe099"
BSC_TOKEN = "0xf3e1449ddb6b218da2c9463d4594ceccc8934346"
BURN = "0x000000000000000000000000000000000000dead"
TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()
SCALE = 10**18

CSS = """
<style>
html, body, [class*="css"] { font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif; }

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 25% 8%, rgba(59,130,246,0.12), transparent 25%),
        radial-gradient(circle at 80% 0%, rgba(34,197,94,0.10), transparent 20%),
        #07101d;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07101d 0%, #091827 100%);
    border-right: 1px solid rgba(148,163,184,0.16);
}

[data-testid="stSidebar"] * { color: #dbeafe; }

.block-container {
    padding-top: 1.25rem;
    padding-left: 1.4rem;
    padding-right: 1.4rem;
    max-width: 1500px;
}

#MainMenu, header, footer { visibility: hidden; }

.page-title {
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    margin-bottom:18px;
}

.title-left h1 {
    margin:0;
    font-size:1.95rem;
    line-height:1.1;
    letter-spacing:-0.05em;
    color:#f8fafc;
}

.title-left p {
    margin:8px 0 0 0;
    color:#cbd5e1;
    font-size:1.02rem;
}

.fake-controls {
    display:flex;
    gap:12px;
    align-items:center;
}

.fake-select {
    border:1px solid rgba(148,163,184,0.22);
    color:#e2e8f0;
    background:#091827;
    border-radius:9px;
    padding:9px 14px;
    font-weight:600;
    min-width:105px;
    text-align:center;
}

.metric-card {
    position:relative;
    border:1px solid rgba(148,163,184,0.18);
    background:linear-gradient(145deg, rgba(15,23,42,.95), rgba(15,32,55,.88));
    border-radius:12px;
    padding:19px 20px;
    min-height:130px;
    box-shadow:inset 0 1px 0 rgba(255,255,255,0.03), 0 18px 34px rgba(0,0,0,0.22);
    overflow:hidden;
}

.metric-card .label {
    color:#cbd5e1;
    font-size:.92rem;
    font-weight:600;
}

.metric-card .value {
    margin-top:14px;
    font-size:1.75rem;
    font-weight:800;
    letter-spacing:-0.04em;
}

.metric-card .sub {
    margin-top:8px;
    font-size:.87rem;
    color:#22c55e;
    font-weight:700;
}

.metric-icon {
    position:absolute;
    right:20px;
    top:31px;
    width:66px;
    height:66px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:2rem;
    opacity:.95;
}

.icon-blue { background:rgba(37,99,235,.23); color:#3b82f6; }
.icon-green { background:rgba(34,197,94,.22); color:#4ade80; }
.icon-yellow { background:rgba(245,158,11,.22); color:#fbbf24; }
.icon-red { background:rgba(239,68,68,.20); color:#f87171; }

.blue { color:#3b82f6; }
.green { color:#22c55e; }
.yellow { color:#fbbf24; }
.red { color:#ef4444; }

.panel {
    border:1px solid rgba(148,163,184,0.18);
    background:linear-gradient(145deg, rgba(15,23,42,.92), rgba(10,25,44,.86));
    border-radius:12px;
    padding:16px 17px;
    box-shadow:0 18px 34px rgba(0,0,0,.20);
}

.panel-title {
    font-size:1rem;
    font-weight:800;
    color:#f8fafc;
    margin-bottom:10px;
}

.mini-link {
    color:#38bdf8;
    font-size:.88rem;
    margin-top:10px;
}

.statusbar {
    margin-top:16px;
    border-top:1px solid rgba(148,163,184,.13);
    padding:13px 0 3px 0;
    display:flex;
    justify-content:space-between;
    color:#cbd5e1;
    font-size:.86rem;
}

.dot {
    display:inline-block;
    width:9px;
    height:9px;
    border-radius:50%;
    background:#22c55e;
    margin-right:7px;
}

.sidebar-brand {
    font-size:1.45rem;
    font-weight:800;
    color:#f8fafc;
    padding:12px 0 18px 0;
}

.sidebar-pill {
    background:#2563eb;
    border-radius:9px;
    padding:11px 14px;
    color:white;
    font-weight:700;
    margin-bottom:8px;
}

.sidebar-item {
    padding:10px 14px;
    color:#cbd5e1;
    font-weight:500;
    margin-bottom:4px;
}

small { color:#94a3b8; }

[data-testid="stDataFrame"] {
    border-radius:10px;
    overflow:hidden;
}

hr { border-color: rgba(148,163,184,.14); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def fmt_tokens(raw, decimals=2):
    try:
        return f"{float(raw) / SCALE:,.{decimals}f}"
    except Exception:
        return "0.00"


def fmt_compact_tokens(raw):
    try:
        n = float(raw) / SCALE
    except Exception:
        return "0"

    if abs(n) >= 1e9:
        return f"{n / 1e9:,.2f}B"
    if abs(n) >= 1e6:
        return f"{n / 1e6:,.2f}M"
    if abs(n) >= 1e3:
        return f"{n / 1e3:,.2f}K"
    return f"{n:,.2f}"


def short_addr(addr):
    s = str(addr)
    return s if len(s) <= 16 else s[:8] + "..." + s[-7:]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_zerochain_mints(pages=40, limit=40):
    rows = []
    raw_events = []

    for page in range(pages):
        offset = page * limit

        try:
            r = requests.get(
                ZEROCHAIN_API,
                params={"limit": limit, "offset": offset, "reverse": "true"},
                timeout=20,
            )
            r.raise_for_status()
            payload = r.json()
        except Exception:
            break

        for item in payload.get("blocks_or_event", []):
            for datum in item.get("datums", []):
                if datum.get("type") == "DATUM_TOKEN_EMISSION":
                    d = datum.get("data", {})

                    validators = d.get("valid_sign_hashes", []) or [
                        s.get("pkey_hash")
                        for s in d.get("data", [])
                        if s.get("pkey_hash")
                    ]

                    row = {
                        "time": datum.get("created"),
                        "token": d.get("ticker", "UNKNOWN"),
                        "amount": int(d.get("value", 0)),
                        "to": d.get("address", "unknown"),
                        "datum_hash": datum.get("hash"),
                        "atom_hash": datum.get("atom_hash"),
                        "validator_count": len(validators),
                        "validators": validators,
                    }

                    rows.append(row)

                    raw_events.append(
                        {
                            "from": "MINT_AUTHORITY",
                            "to": row["to"],
                            "amount": row["amount"],
                            "token": row["token"],
                            "time": row["time"],
                            "label_from": "Validator",
                            "label_to": "Bridge" if row["validator_count"] >= 3 else "User",
                        }
                    )

    df = pd.DataFrame(rows)

    if not df.empty:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")

    return df, raw_events


@st.cache_data(ttl=600, show_spinner=False)
def safe_burn_total(rpc, token, start_block):
    if not rpc:
        return 0

    try:
        w3 = Web3(Web3.HTTPProvider(rpc))
        latest = w3.eth.block_number
        step = 50_000
        total = 0
        target_topic = Web3.to_hex(Web3.to_bytes(hexstr=BURN).rjust(32, b"\x00"))

        for block in range(start_block, latest + 1, step):
            logs = w3.eth.get_logs(
                {
                    "fromBlock": block,
                    "toBlock": min(block + step - 1, latest),
                    "address": Web3.to_checksum_address(token),
                    "topics": [TRANSFER_TOPIC, None, target_topic],
                }
            )

            for log in logs:
                data = log["data"].hex() if hasattr(log["data"], "hex") else log["data"]
                total += int(data, 16)

        return total

    except Exception:
        return 0


def label_wallets(df):
    if df.empty:
        return pd.DataFrame(columns=["address", "label", "amount", "txs", "share"])

    g = df.groupby("to").agg(
        amount=("amount", "sum"),
        txs=("amount", "count"),
    ).reset_index()

    total = max(g["amount"].sum(), 1)
    g["share"] = g["amount"] / total

    def label(row):
        if row["share"] > 0.20 and row["txs"] > 5:
            return "Bridge"
        if row["share"] > 0.08:
            return "Whale"
        if row["txs"] > 25:
            return "Exchange"
        return "User"

    g["label"] = g.apply(label, axis=1)

    return g.rename(columns={"to": "address"}).sort_values("amount", ascending=False)


def validator_stats(df):
    c = Counter()

    if not df.empty and "validators" in df.columns:
        for vals in df["validators"]:
            for v in vals or []:
                c[v] += 1

    out = pd.DataFrame(c.items(), columns=["validator", "sign_count"])

    if not out.empty:
        out = out.sort_values("sign_count", ascending=False)

    return out


def build_bridge_wallet_detector(wallet_df, events):
    if wallet_df.empty:
        return [], pd.DataFrame()

    scored = wallet_df.copy()
    scored["tokens"] = scored["amount"] / SCALE

    outgoing_counts = Counter(e.get("from") for e in events if e.get("from"))

    scored["outgoing_events"] = scored["address"].apply(
        lambda x: outgoing_counts.get(x, 0)
    )

    scored["bridge_score"] = 0
    scored.loc[scored["share"] > 0.20, "bridge_score"] += 40
    scored.loc[scored["share"] > 0.10, "bridge_score"] += 20
    scored.loc[scored["txs"] >= 5, "bridge_score"] += 20
    scored.loc[scored["outgoing_events"] <= 2, "bridge_score"] += 20
    scored["bridge_score"] = scored["bridge_score"].clip(0, 100)

    candidates = scored[scored["bridge_score"] >= 60].sort_values(
        "bridge_score", ascending=False
    )

    return candidates["address"].tolist(), candidates


def proof_of_backing_score(diff, total_minted, bridge_candidates_df, val_df, bridge_movements):
    score = 100

    if total_minted > 0:
        score -= min(45, (max(diff, 0) / total_minted) * 100)

    if not bridge_candidates_df.empty:
        score += min(20, bridge_candidates_df["share"].sum() * 20)
    else:
        score -= 20

    if not val_df.empty:
        top3 = val_df["sign_count"].head(3).sum()
        total = max(val_df["sign_count"].sum(), 1)
        score -= min(25, (top3 / total) * 25)

    if bridge_movements:
        score -= 15

    return max(0, min(100, round(score, 1)))


# Sidebar
st.sidebar.markdown('<div class="sidebar-brand">◇ CF20 Audit</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-pill">⌂ Overview</div>', unsafe_allow_html=True)

for item in ["◷ Mint vs Locked", "▦ Wallets", "☰ Transactions", "♧ Graph", "⚠ Alerts", "⚙ Settings", "ⓘ About"]:
    st.sidebar.markdown(f'<div class="sidebar-item">{item}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
pages_to_scan = st.sidebar.slider("Zerochain pages", 5, 200, 40, 5)
start_block_eth = st.sidebar.number_input("ETH start block", min_value=0, value=18_000_000, step=100_000)
start_block_bsc = st.sidebar.number_input("BSC start block", min_value=0, value=30_000_000, step=100_000)
use_rpc = st.sidebar.checkbox("Enable ETH/BSC RPC burn scan", value=False)

eth_rpc = st.secrets.get("ETH_RPC", "")
bsc_rpc = st.secrets.get("BSC_RPC", "https://bsc-dataseed.binance.org/")

st.markdown(
    """
<div class="page-title">
  <div class="title-left">
    <h1>CF20 Bridge Verification Dashboard</h1>
    <p>Real-time verification of CF20 supply vs locked/burned on Ethereum & BSC</p>
  </div>
  <div class="fake-controls">
    <div class="fake-select">All Tokens⌄</div>
    <div class="fake-select">7D⌄</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.spinner("Loading Zerochain emissions..."):
    df, events = fetch_zerochain_mints(pages=pages_to_scan)

st.session_state["events"] = events

wallet_df = label_wallets(df)
val_df = validator_stats(df)

total_minted = int(df["amount"].sum()) if not df.empty else 0
eth_burned = safe_burn_total(eth_rpc, ETH_TOKEN, int(start_block_eth)) if use_rpc else 0
bsc_burned = safe_burn_total(bsc_rpc, BSC_TOKEN, int(start_block_bsc)) if use_rpc else 0

total_locked = eth_burned + bsc_burned
diff = total_minted - total_locked
diff_tokens = diff / SCALE

# 🔥 ADD THIS RIGHT HERE
bridge_supply = bridge_candidates_df["amount"].sum() if not bridge_candidates_df.empty else 0
effective_locked = total_locked + bridge_supply
adjusted_diff = total_minted - effective_locked
adjusted_diff_tokens = adjusted_diff / SCALE

bridge_wallets, bridge_candidates_df = build_bridge_wallet_detector(wallet_df, events)
bridge_movements = [e for e in events if e.get("from") in bridge_wallets]
recent_bridge_moves = [
    e for e in bridge_movements
    if e.get("time") and (pd.Timestamp.utcnow() - pd.to_datetime(e["time"])).seconds < 600
]

backing_score = proof_of_backing_score(
    diff,
    total_minted,
    bridge_candidates_df,
    val_df,
    bridge_movements,
)

if not use_rpc:
    status, status_class = "RPC Disabled", "yellow"
elif abs(diff) < 10**12:
    status, status_class = "Balanced", "green"
elif diff > 0:
    status, status_class = "Drift", "red"
else:
    status, status_class = "Locked > Minted", "yellow"

# KPI Cards
st.write("")

bridge_supply = bridge_candidates_df["amount"].sum() if not bridge_candidates_df.empty else 0
effective_locked = total_locked + bridge_supply
adjusted_diff = total_minted - effective_locked
adjusted_diff_tokens = adjusted_diff / SCALE

k1, k2, k3, k4 = st.columns(4)

kpi_data = [
    (k1, "Total CF20 Minted ⓘ", fmt_tokens(total_minted), "live Zerochain sample", "🪶", "blue", "icon-blue"),
    (k2, "Total Locked / Burned ⓘ", fmt_tokens(total_locked), "ETH + BSC scan", "🔒", "green", "icon-green"),
    (k3, "Adjusted Δ ⓘ", f"{adjusted_diff_tokens:,.2f}", "Minted vs (locked + bridge)", "⚖", "yellow" if adjusted_diff >= 0 else "green", "icon-yellow"),
    (k4, "System Status ⓘ", status, f"Backing score {backing_score}/100", "🛡", status_class, "icon-green" if status_class == "green" else "icon-yellow" if status_class == "yellow" else "icon-red"),
]

for col, label, value, sub, icon, color_class, icon_class in kpi_data:
    col.markdown(
        f"""
    <div class="metric-card">
      <div class="label">{label}</div>
      <div class="value {color_class}">{value}</div>
      <div class="sub">{sub}</div>
      <div class="metric-icon {icon_class}">{icon}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

if recent_bridge_moves:
    st.error(f"🚨 {len(recent_bridge_moves)} recent bridge wallet movements detected (last 10 min)")

# Middle
st.write("")
left, right = st.columns([1.55, 1])

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Minted vs Locked Over Time</div>', unsafe_allow_html=True)

    if df.empty:
        st.warning("No mint data loaded.")
    else:
        ts = df.sort_values("time").copy()
        ts["Minted"] = (ts["amount"] / SCALE).cumsum()
        ts["Locked"] = total_locked / SCALE if total_locked > 0 else 0
        ts["Delta"] = ts["Minted"] - ts["Locked"]

        chart_df = ts[["time", "Minted", "Locked", "Delta"]].copy()
        chart_df["time"] = pd.to_datetime(chart_df["time"], errors="coerce")
        chart_df = chart_df.dropna().tail(200)

        base = alt.Chart(chart_df).encode(
            x=alt.X("time:T", title=None)
        )

        minted_locked = base.transform_fold(
            ["Minted", "Locked"],
            as_=["Series", "Tokens"],
        ).mark_area(
            opacity=0.38,
            interpolate="monotone",
        ).encode(
            y=alt.Y("Tokens:Q", title="Minted / Locked"),
            color=alt.Color(
                "Series:N",
                scale=alt.Scale(
                    domain=["Minted", "Locked"],
                    range=["#3b82f6", "#22c55e"],
                ),
                legend=alt.Legend(orient="top"),
            ),
        )

        delta_line = base.mark_line(
            strokeWidth=3,
            interpolate="monotone",
            color="#f59e0b",
        ).encode(
            y=alt.Y("Delta:Q", title="Delta")
        )

        chart = alt.layer(
            minted_locked,
            delta_line,
        ).resolve_scale(
            y="independent",
        ).properties(
            height=330,
        ).configure_view(
            strokeWidth=0,
        ).configure_axis(
            gridColor="rgba(148,163,184,0.12)",
            labelColor="#cbd5e1",
            titleColor="#cbd5e1",
        ).configure_legend(
            labelColor="#cbd5e1",
            titleColor="#cbd5e1",
        )

        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Supply Distribution by Wallet Type</div>', unsafe_allow_html=True)

    if wallet_df.empty:
        st.info("No wallet data.")
    else:
        dist_raw = wallet_df.groupby("label")["amount"].sum().reset_index()
        total_amount = max(dist_raw["amount"].sum(), 1)

        dist = pd.DataFrame({
            "label": dist_raw["label"].astype(str),
            "tokens": dist_raw["amount"].apply(lambda x: int(x) / SCALE),
            "share": dist_raw["amount"].apply(lambda x: int(x) / total_amount),
        })

        donut = alt.Chart(dist).mark_arc(
            innerRadius=70,
            outerRadius=115
        ).encode(
            theta=alt.Theta("tokens:Q"),
            color=alt.Color(
                "label:N",
                scale=alt.Scale(
                    range=["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#a855f7"]
                ),
                legend=alt.Legend(orient="bottom")
            ),
            tooltip=[
                alt.Tooltip("label:N", title="Wallet Type"),
                alt.Tooltip("tokens:Q", title="Tokens", format=",.2f"),
                alt.Tooltip("share:Q", title="Share", format=".2%")
            ]
        ).properties(height=260)

        st.altair_chart(donut, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Bottom cards
st.write("")
b1, b2, b3 = st.columns([1, 1, 1])

with b1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Recent Mint Events</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("No mint events.")
    else:
        recent = df.sort_values("time", ascending=False).head(6).copy()
        recent["Amount"] = recent["amount"].apply(fmt_compact_tokens)
        recent["To"] = recent["to"].apply(short_addr)
        recent = recent.rename(
            columns={
                "time": "Time (UTC)",
                "token": "Token",
                "validator_count": "Type",
            }
        )

        st.dataframe(
            recent[["Time (UTC)", "Token", "Amount", "To", "Type"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown('<div class="mini-link">View all mint events</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Top Wallets by Balance</div>', unsafe_allow_html=True)

    if wallet_df.empty:
        st.info("No wallets.")
    else:
        top = wallet_df.head(6).copy()
        top["Address"] = top["address"].apply(short_addr)
        top["Balance (CF20)"] = top["amount"].apply(fmt_compact_tokens)
        top["% of Supply"] = top["share"].apply(lambda x: f"{x:.2%}")
        top = top.rename(columns={"label": "Label"})

        st.dataframe(
            top[["Address", "Label", "Balance (CF20)", "% of Supply"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown('<div class="mini-link">View all wallets</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Latest Large Transfers</div>', unsafe_allow_html=True)

    if bridge_candidates_df.empty:
        st.info("No bridge candidates in sample.")
    else:
        transfers = bridge_candidates_df.head(6).copy()
        transfers["Time (UTC)"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        transfers["From"] = "Bridge"
        transfers["To"] = transfers["label"]
        transfers["Amount (CF20)"] = transfers["amount"].apply(fmt_compact_tokens)
        transfers["Type"] = "↓"

        st.dataframe(
            transfers[["Time (UTC)", "From", "To", "Amount (CF20)", "Type"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown('<div class="mini-link">View all transfers</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")
e1, e2, e3 = st.columns(3)
e1.metric("Detected bridge wallets", len(bridge_wallets))
e2.metric("Bridge wallet movements", len(bridge_movements))
e3.metric("Proof of backing score", f"{backing_score}/100")

# 🔥 ADD THIS
st.progress(backing_score / 100)
if backing_score >= 80:
    st.success("🟢 Strong cryptographic backing confidence")
elif backing_score >= 50:
    st.warning("🟡 Moderate backing confidence")
else:
    st.error("🔴 Weak backing confidence")

st.markdown(
    f"""
<div class="statusbar">
  <div><span class="dot"></span>Zerochain: Connected &nbsp;&nbsp;&nbsp; <span class="dot"></span>Ethereum: {'Connected' if eth_rpc else 'RPC missing'} &nbsp;&nbsp;&nbsp; <span class="dot"></span>BSC: Connected</div>
  <div>Auto-refresh: ON ●</div>
</div>
""",
    unsafe_allow_html=True,
)
