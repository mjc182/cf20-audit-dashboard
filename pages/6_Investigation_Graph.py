import gzip
import json
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from streamlit_agraph import agraph, Node, Edge, Config
    HAS_AGRAPH = True
except Exception:
    HAS_AGRAPH = False

st.set_page_config(page_title="Wallet Investigation Graph", layout="wide")

DATA_DIR = Path("data")
ETH_GZ = DATA_DIR / "eth_transfers.jsonl.gz"
ETH_JSONL = DATA_DIR / "eth_transfers.jsonl"
SCALE = 10**18

st.title("🧬 Interactive Wallet Investigation Graph")
st.caption("Click-through wallet tracing for CELL bridge flows.")

def pick_data_file():
    if ETH_GZ.exists():
        return ETH_GZ
    if ETH_JSONL.exists():
        return ETH_JSONL
    return None

DATA_FILE = pick_data_file()

if DATA_FILE is None:
    st.error(
        "Missing ETH transfer data. Upload either "
        "`data/eth_transfers.jsonl.gz` or `data/eth_transfers.jsonl`."
    )
    st.stop()

@st.cache_data(show_spinner=False)
def load_transfers(path_str):
    path = Path(path_str)
    opener = gzip.open if path.suffix == ".gz" else open

    rows = []
    with opener(path, "rt") as f:
        for line in f:
            try:
                tx = json.loads(line)
                rows.append({
                    "from": str(tx["from"]).lower(),
                    "to": str(tx["to"]).lower(),
                    "amount": int(tx["amount"]) / SCALE,
                    "tx_hash": tx.get("tx_hash", ""),
                    "block": tx.get("block", ""),
                    "chain": tx.get("chain", "eth"),
                })
            except Exception:
                continue

    return pd.DataFrame(rows)

df = load_transfers(str(DATA_FILE))

st.success(f"Loaded {len(df):,} transfers from `{DATA_FILE}`")

known_labels = {
    "0x4a831a8ebb160ad025d34a788c99e9320b9ab531": "Bridge Intake",
    "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60": "Aggregator L1",
    "0x50ebb0827aa80ba1a2a30b38581629996262d481": "Aggregator L2",
    "0x52105eee8e836ff9e60cb02c0a665cbe2fc3a30d": "Secondary Distributor",
    "0x9c4cc862f51b1ba90485de3502aa058ca4331f32": "Router / Exchange-like",
}

default_wallet = "0x4a831a8ebb160ad025d34a788c99e9320b9ab531"

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    wallet = st.text_input("Target wallet", value=default_wallet).lower().strip()
with c2:
    min_amount = st.number_input("Minimum flow amount", min_value=0, value=1000, step=500)
with c3:
    max_edges = st.number_input("Max edges", min_value=10, max_value=300, value=100, step=10)

def short(addr):
    return addr[:6] + "..." + addr[-4:]

def label(addr):
    return known_labels.get(addr.lower(), short(addr))

def node_color(addr, center):
    addr = addr.lower()
    if addr == center:
        return "#ef4444"
    if addr in known_labels:
        return "#f59e0b"
    return "#2563eb"

related = df[(df["from"] == wallet) | (df["to"] == wallet)].copy()

if related.empty:
    st.warning("No transfers found for this target wallet in the loaded file.")
    st.stop()

edges_agg = (
    related.groupby(["from", "to"], as_index=False)
    .agg(amount=("amount", "sum"), txs=("amount", "count"))
    .query("amount >= @min_amount")
    .sort_values("amount", ascending=False)
    .head(int(max_edges))
)

if edges_agg.empty:
    st.warning("No edges matched the minimum amount filter.")
    st.stop()

st.markdown("### Flow Graph")

if HAS_AGRAPH:
    nodes = {}
    graph_edges = []

    for _, row in edges_agg.iterrows():
        src = row["from"]
        dst = row["to"]
        amt = row["amount"]

        nodes[src] = Node(
            id=src,
            label=label(src),
            size=42 if src == wallet else 24,
            color=node_color(src, wallet),
        )
        nodes[dst] = Node(
            id=dst,
            label=label(dst),
            size=42 if dst == wallet else 24,
            color=node_color(dst, wallet),
        )

        graph_edges.append(
            Edge(
                source=src,
                target=dst,
                label=f"{amt:,.0f}",
                color="#94a3b8",
            )
        )

    config = Config(
        width=1200,
        height=700,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#fde047",
        collapsible=True,
    )

    selected = agraph(nodes=list(nodes.values()), edges=graph_edges, config=config)
else:
    st.info("streamlit-agraph is not installed, showing table view instead.")
    selected = None

st.markdown("### Wallet Inspector")

inspect = selected if selected else wallet

incoming = df[df["to"] == inspect].copy()
outgoing = df[df["from"] == inspect].copy()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Incoming txs", len(incoming))
m2.metric("Outgoing txs", len(outgoing))
m3.metric("Incoming CELL", f"{incoming['amount'].sum():,.2f}")
m4.metric("Outgoing CELL", f"{outgoing['amount'].sum():,.2f}")

st.code(inspect)

st.markdown("### Top Incoming")
if incoming.empty:
    st.info("No incoming transfers.")
else:
    show = incoming.sort_values("amount", ascending=False).head(25)
    st.dataframe(show, use_container_width=True, hide_index=True)

st.markdown("### Top Outgoing")
if outgoing.empty:
    st.info("No outgoing transfers.")
else:
    show = outgoing.sort_values("amount", ascending=False).head(25)
    st.dataframe(show, use_container_width=True, hide_index=True)

st.markdown("### Top Direct Edges")
show_edges = edges_agg.copy()
show_edges["from_label"] = show_edges["from"].apply(label)
show_edges["to_label"] = show_edges["to"].apply(label)
show_edges["amount"] = show_edges["amount"].apply(lambda x: f"{float(x):,.2f}")
st.dataframe(
    show_edges[["from_label", "to_label", "from", "to", "amount", "txs"]],
    use_container_width=True,
    hide_index=True,
)
