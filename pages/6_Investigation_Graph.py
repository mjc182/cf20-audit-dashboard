import json
from collections import defaultdict
from pathlib import Path

import networkx as nx
import pandas as pd
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(page_title="Wallet Investigation Graph", layout="wide")

DATA_FILE = Path("data/eth_transfers.jsonl")
SCALE = 10**18

st.title("🧬 Interactive Wallet Investigation Graph")
st.caption("Click-through wallet tracing for CELL bridge flows.")

if not DATA_FILE.exists():
    st.error("Missing data/eth_transfers.jsonl. Run the ETH scanner first.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_transfers():
    rows = []
    with DATA_FILE.open() as f:
        for line in f:
            tx = json.loads(line)
            rows.append({
                "from": tx["from"].lower(),
                "to": tx["to"].lower(),
                "amount": int(tx["amount"]) / SCALE,
                "tx_hash": tx["tx_hash"],
                "block": tx["block"],
            })
    return pd.DataFrame(rows)

df = load_transfers()

known_labels = {
    "0x4a831a8ebb160ad025d34a788c99e9320b9ab531": "Bridge Operator",
    "0x35ce1677d3d6aaaacd96510704d3c8617a12ee60": "Aggregator L1",
    "0x50ebb0827aa80ba1a2a30b38581629996262d481": "Aggregator L2",
    "0x9c4cc862f51b1ba90485de3502aa058ca4331f32": "Exchange / Router",
}

default_wallet = "0x4a831a8ebb160ad025d34a788c99e9320b9ab531"

wallet = st.text_input("Target wallet", value=default_wallet).lower().strip()
min_amount = st.slider("Minimum flow amount", 0, 100000, 1000, 500)
depth = st.slider("Trace depth", 1, 3, 2)
max_edges = st.slider("Max edges", 10, 200, 80, 10)

def short(addr):
    return addr[:6] + "..." + addr[-4:]

def label(addr):
    return known_labels.get(addr, short(addr))

def node_color(addr, center):
    if addr == center:
        return "#ef4444"
    if addr in known_labels:
        return "#f59e0b"
    return "#2563eb"

def build_trace(seed, depth):
    seen = {seed}
    frontier = {seed}
    edges = defaultdict(float)

    for _ in range(depth):
        next_frontier = set()

        related = df[
            (df["from"].isin(frontier)) |
            (df["to"].isin(frontier))
        ]

        for _, row in related.iterrows():
            amt = row["amount"]
            if amt < min_amount:
                continue

            src = row["from"]
            dst = row["to"]

            edges[(src, dst)] += amt

            if src not in seen:
                next_frontier.add(src)
            if dst not in seen:
                next_frontier.add(dst)

            seen.add(src)
            seen.add(dst)

        frontier = next_frontier

    sorted_edges = sorted(edges.items(), key=lambda x: x[1], reverse=True)[:max_edges]
    return sorted_edges

flows = build_trace(wallet, depth)

nodes = {}
edges = []

for (src, dst), amt in flows:
    nodes[src] = Node(
        id=src,
        label=label(src),
        size=38 if src == wallet else 22,
        color=node_color(src, wallet),
    )
    nodes[dst] = Node(
        id=dst,
        label=label(dst),
        size=38 if dst == wallet else 22,
        color=node_color(dst, wallet),
    )

    edges.append(
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

selected = agraph(
    nodes=list(nodes.values()),
    edges=edges,
    config=config,
)

st.markdown("### Wallet Inspector")

inspect = selected if selected else wallet

incoming = df[df["to"] == inspect].copy()
outgoing = df[df["from"] == inspect].copy()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Incoming txs", len(incoming))
c2.metric("Outgoing txs", len(outgoing))
c3.metric("Incoming CELL", f"{incoming['amount'].sum():,.2f}")
c4.metric("Outgoing CELL", f"{outgoing['amount'].sum():,.2f}")

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

st.markdown("### Verdict Helper")

in_total = incoming["amount"].sum()
out_total = outgoing["amount"].sum()
ratio = out_total / in_total if in_total else 0
unique_senders = incoming["from"].nunique()
unique_receivers = outgoing["to"].nunique()

if in_total > 10000 and ratio < 0.1 and unique_senders >= 10:
    st.success("Possible custody / lock wallet pattern.")
elif ratio > 0.75:
    st.error("Router / pass-through wallet pattern.")
elif out_total == 0 and unique_senders <= 3:
    st.warning("Internal stash / holding wallet pattern.")
else:
    st.info("Aggregator / mixed-flow wallet pattern.")

st.write({
    "pass_through_ratio": round(ratio, 4),
    "unique_senders": int(unique_senders),
    "unique_receivers": int(unique_receivers),
})
