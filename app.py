
import math
from collections import Counter, defaultdict
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from web3 import Web3

st.set_page_config(
    page_title="CF20 Public Audit Dashboard",
    page_icon="🧬",
    layout="wide",
)

ZEROCHAIN_API = "https://2.api.explorer.cellframe.net/atoms/Backbone/zerochain/"
ETH_TOKEN = "0x26c8afbbfe1ebaca03c2bb082e69d0476bffe099"
BSC_TOKEN = "0xf3e1449ddb6b218da2c9463d4594ceccc8934346"
BURN = "0x000000000000000000000000000000000000dead"
TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()

CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(34,197,94,0.14), transparent 30%),
        radial-gradient(circle at top right, rgba(59,130,246,0.12), transparent 28%),
        #070b12;
}
[data-testid="stSidebar"] {
    background: #0b1220;
}
.block-container {
    padding-top: 1.8rem;
}
.hero {
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 24px;
    padding: 26px 28px;
    background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(17,24,39,0.82));
    box-shadow: 0 18px 60px rgba(0,0,0,0.36);
}
.hero h1 {
    margin: 0;
    font-size: 2.4rem;
    letter-spacing: -0.04em;
}
.hero p {
    color: #94a3b8;
    margin-top: 8px;
    font-size: 1.02rem;
}
.badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.38);
    color: #86efac;
    font-size: 0.82rem;
    margin-bottom: 12px;
}
.metric-card {
    border: 1px solid rgba(148,163,184,0.2);
    background: rgba(15,23,42,0.82);
    border-radius: 22px;
    padding: 18px;
    min-height: 118px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.24);
}
.metric-card .label {
    color: #94a3b8;
    font-size: .86rem;
}
.metric-card .value {
    color: #f8fafc;
    font-size: 1.65rem;
    font-weight: 800;
    margin-top: 8px;
}
.metric-card .sub {
    color: #64748b;
    font-size: .78rem;
    margin-top: 7px;
}
.panel {
    border: 1px solid rgba(148,163,184,0.2);
    background: rgba(15,23,42,0.78);
    border-radius: 22px;
    padding: 18px 20px;
    box-shadow: 0 10px 32px rgba(0,0,0,0.24);
}
.status-ok {
    color: #86efac;
}
.status-warn {
    color: #fde68a;
}
.status-bad {
    color: #fca5a5;
}
small {
    color: #94a3b8;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

def fmt_num(n):
    try:
        n = float(n)
    except Exception:
        return "0"
    if abs(n) >= 1e18:
        return f"{n/1e18:,.2f}e18"
    if abs(n) >= 1e12:
        return f"{n/1e12:,.2f}T"
    if abs(n) >= 1e9:
        return f"{n/1e9:,.2f}B"
    if abs(n) >= 1e6:
        return f"{n/1e6:,.2f}M"
    return f"{n:,.0f}"

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

        items = payload.get("blocks_or_event", [])
        if not items:
            break

        for item in items:
            for datum in item.get("datums", []):
                if datum.get("type") == "DATUM_TOKEN_EMISSION":
                    d = datum.get("data", {})
                    validators = d.get("valid_sign_hashes", []) or [
                        s.get("pkey_hash") for s in d.get("data", []) if s.get("pkey_hash")
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
                    raw_events.append({
                        "from": "MINT_AUTHORITY",
                        "to": row["to"],
                        "amount": row["amount"],
                        "token": row["token"],
                        "time": row["time"],
                        "label_from": "Validator",
                        "label_to": "Bridge" if row["validator_count"] >= 3 else "User",
                    })

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
            logs = w3.eth.get_logs({
                "fromBlock": block,
                "toBlock": min(block + step - 1, latest),
                "address": Web3.to_checksum_address(token),
                "topics": [TRANSFER_TOPIC, None, target_topic],
            })
            total += sum(int(log["data"].hex() if hasattr(log["data"], "hex") else log["data"], 16) for log in logs)
        return total
    except Exception:
        return 0

def label_wallets(df):
    if df.empty:
        return pd.DataFrame(columns=["address", "label", "amount", "txs", "share"])
    g = df.groupby("to").agg(amount=("amount", "sum"), txs=("amount", "count")).reset_index()
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

st.sidebar.title("CF20 Audit")
pages_to_scan = st.sidebar.slider("Zerochain pages to scan", 5, 200, 40, 5)
start_block_eth = st.sidebar.number_input("ETH start block", min_value=0, value=18_000_000, step=100_000)
start_block_bsc = st.sidebar.number_input("BSC start block", min_value=0, value=30_000_000, step=100_000)
use_rpc = st.sidebar.checkbox("Enable ETH/BSC RPC burn scan", value=False)

eth_rpc = st.secrets.get("ETH_RPC", "") if hasattr(st, "secrets") else ""
bsc_rpc = st.secrets.get("BSC_RPC", "https://bsc-dataseed.binance.org/") if hasattr(st, "secrets") else ""

st.markdown("""
<div class="hero">
  <div class="badge">Public on-chain intelligence</div>
  <h1>CF20 Public Audit Dashboard</h1>
  <p>Independent visibility into Zerochain emissions, validator authorization, wallet concentration, graph clusters, and suspicious flow patterns.</p>
</div>
""", unsafe_allow_html=True)

with st.spinner("Loading Zerochain emissions..."):
    df, events = fetch_zerochain_mints(pages=pages_to_scan)

# persist for graph page
st.session_state["events"] = events

wallet_df = label_wallets(df)
val_df = validator_stats(df)

total_minted = int(df["amount"].sum()) if not df.empty else 0
eth_burned = safe_burn_total(eth_rpc, ETH_TOKEN, int(start_block_eth)) if use_rpc else 0
bsc_burned = safe_burn_total(bsc_rpc, BSC_TOKEN, int(start_block_bsc)) if use_rpc else 0
total_locked = eth_burned + bsc_burned
diff = total_minted - total_locked

if not use_rpc:
    status = "RPC scan disabled"
    status_class = "status-warn"
elif abs(diff) < 10**12:
    status = "Balanced"
    status_class = "status-ok"
elif diff > 0:
    status = "Potential excess minting"
    status_class = "status-bad"
else:
    status = "Locked > minted"
    status_class = "status-warn"

st.write("")
diff = total_minted - total_locked
diff_tokens = diff / 1e18
c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"""
<div class="metric-card">
  <div class="label">CF20 minted</div>
  <div class="value">{fmt_num(total_minted)}</div>
  <div class="sub">Zerochain DATUM_TOKEN_EMISSION</div>
</div>
""", unsafe_allow_html=True)

c2.markdown(f"""
<div class="metric-card">
  <div class="label">ETH/BSC locked</div>
  <div class="value">{fmt_num(total_locked)}</div>
  <div class="sub">Burn/lock scan via RPC</div>
</div>
""", unsafe_allow_html=True)

c3.markdown(f"""
<div class="metric-card">
  <div class="label">Difference</div>
  <div class="value">{diff_tokens:,.2f} tokens</div>
  <div class="sub">Minted minus locked</div>
</div>
""", unsafe_allow_html=True)

c4.markdown(f"""
<div class="metric-card">
  <div class="label">Audit status</div>
  <div class="value {status_class}">{status}</div>
  <div class="sub">Current dashboard assessment</div>
</div>
""", unsafe_allow_html=True)
    col.markdown(f"""
    <div class="metric-card">
      <div class="label">{label}</div>
      <div class="value {status_class if label == "Audit status" else ""}">{value}</div>
      <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
left, right = st.columns([1.45, 1])

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Minted Supply Over Time")
    if df.empty:
        st.warning("No mint data loaded.")
    else:
        ts = df.sort_values("time").copy()

# Scale huge raw token units down so Streamlit/Arrow can chart safely
SCALE = 10**18
ts["amount_scaled"] = ts["amount"].apply(lambda x: int(x) / SCALE)
ts["cumulative"] = ts["amount_scaled"].cumsum()

st.line_chart(ts.set_index("time")["cumulative"], height=310)
st.caption("Chart values are scaled by 1e18 raw units.")
st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Validator Power")
    if val_df.empty:
        st.info("No validator signatures found in loaded data.")
    else:
        top3 = val_df["sign_count"].head(3).sum()
        total_signs = max(val_df["sign_count"].sum(), 1)
        concentration = top3 / total_signs
        st.metric("Top 3 signature share", f"{concentration:.1%}")
        st.bar_chart(val_df.set_index("validator").head(10), height=245)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")
a, b = st.columns([1, 1])

with a:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Wallet Intelligence")
    if wallet_df.empty:
        st.info("No wallets loaded.")
    else:
        show = wallet_df.head(20).copy()
        show["amount"] = show["amount"].map(fmt_num)
        show["share"] = show["share"].map(lambda x: f"{x:.2%}")
        st.dataframe(show, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

with b:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Suspicious Mint Events")
    if df.empty:
        st.info("No mint events.")
    else:
        threshold = max(df["amount"].mean() * 10, df["amount"].quantile(0.95))
        spikes = df[df["amount"] >= threshold].sort_values("amount", ascending=False)
        if spikes.empty:
            st.success("No major mint spikes in loaded sample.")
        else:
            tmp = spikes[["time", "token", "amount", "to", "validator_count"]].head(20).copy()
            tmp["amount"] = tmp["amount"].map(fmt_num)
            st.dataframe(tmp, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.markdown("""
<div class="panel">
<h3>Methodology & Limitations</h3>
<small>
Mint activity is extracted from Zerochain <code>DATUM_TOKEN_EMISSION</code> records. Validator concentration is inferred from emission signature hashes.
Wallet labels and suspicious-flow detection are heuristic. A direct cryptographic source-chain tx reference was not observed in the sample emission records, so cross-chain backing is assessed by supply math and behavior rather than direct proof.
</small>
</div>
""", unsafe_allow_html=True)
