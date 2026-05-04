
from collections import defaultdict

import networkx as nx
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(page_title="CF20 Graph Intelligence", layout="wide", page_icon="🧬")

CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(239,68,68,0.13), transparent 28%),
        radial-gradient(circle at top right, rgba(34,197,94,0.12), transparent 30%),
        #070b12;
}
[data-testid="stSidebar"] { background: #0b1220; }
.block-container { padding-top: 1.5rem; }
.panel {
    border: 1px solid rgba(148,163,184,0.2);
    background: rgba(15,23,42,0.8);
    border-radius: 22px;
    padding: 18px 20px;
    box-shadow: 0 10px 32px rgba(0,0,0,0.24);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.title("🧬 Wallet Cluster Graph")
st.caption("Interactive cluster highlighting, suspicious flow detection, and click-to-inspect wallet flows.")

events = st.session_state.get("events", [])

if not events:
    st.warning("No events loaded yet. Open the main dashboard first so it can fetch Zerochain data.")
    st.stop()

def build_graph(events):
    G = nx.DiGraph()
    for e in events:
        src = e.get("from")
        dst = e.get("to")
        amount = int(e.get("amount", 0))
        if not src or not dst:
            continue
        G.add_edge(src, dst, amount=amount, token=e.get("token", "UNKNOWN"), time=e.get("time", ""))
    return G

def detect_clusters(G):
    clusters = list(nx.connected_components(G.to_undirected()))
    cluster_map = {}
    for i, c in enumerate(clusters):
        for node in c:
            cluster_map[node] = i
    return cluster_map, clusters

def detect_suspicious(G):
    suspicious_nodes = set()
    suspicious_edges = set()
    amounts = [d.get("amount", 0) for _, _, d in G.edges(data=True)]
    if not amounts:
        return suspicious_nodes, suspicious_edges
    avg = sum(amounts) / len(amounts)
    spike = max(avg * 10, sorted(amounts)[int(len(amounts) * 0.95) - 1] if len(amounts) > 5 else avg)
    for src, dst, data in G.edges(data=True):
        amount = data.get("amount", 0)
        if amount >= spike:
            suspicious_edges.add((src, dst))
            suspicious_nodes.update([src, dst])
        if G.has_edge(dst, src):
            suspicious_edges.add((src, dst))
            suspicious_edges.add((dst, src))
            suspicious_nodes.update([src, dst])
        if G.out_degree(src) > 25:
            suspicious_nodes.add(src)
    return suspicious_nodes, suspicious_edges

def cluster_color(cid):
    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#a855f7", "#06b6d4", "#84cc16", "#ec4899", "#64748b"]
    return colors[cid % len(colors)]

def short(addr):
    if len(str(addr)) <= 14:
        return str(addr)
    return str(addr)[:7] + "…" + str(addr)[-5:]

G = build_graph(events)
cluster_map, clusters = detect_clusters(G)
suspicious_nodes, suspicious_edges = detect_suspicious(G)

st.sidebar.header("Graph Filters")
cluster_options = ["All"] + list(range(len(clusters)))
selected_cluster = st.sidebar.selectbox("Highlight cluster", cluster_options)
show_only_suspicious = st.sidebar.checkbox("Show only suspicious flows", value=False)
min_amount = st.sidebar.number_input("Minimum amount", min_value=0, value=0)
max_edges = st.sidebar.slider("Max edges", 25, 1000, 250, 25)

nodes = {}
edges = []
count = 0

for src, dst, data in G.edges(data=True):
    if count >= max_edges:
        break
    amount = int(data.get("amount", 0))
    if amount < min_amount:
        continue
    is_suspicious = (src, dst) in suspicious_edges
    if show_only_suspicious and not is_suspicious:
        continue
    if selected_cluster != "All":
        if cluster_map.get(src) != selected_cluster and cluster_map.get(dst) != selected_cluster:
            continue

    for addr in [src, dst]:
        cid = cluster_map.get(addr, 0)
        suspicious = addr in suspicious_nodes
        nodes[addr] = Node(
            id=addr,
            label=short(addr),
            size=30 if suspicious else 16,
            color="#ef4444" if suspicious else cluster_color(cid),
        )

    edges.append(
        Edge(
            source=src,
            target=dst,
            label=str(amount)[:8],
            color="#ef4444" if is_suspicious else "#94a3b8",
        )
    )
    count += 1

config = Config(
    width=1100,
    height=650,
    directed=True,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#FDE047",
    collapsible=True,
)

selected = agraph(nodes=list(nodes.values()), edges=edges, config=config)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Clusters", len(clusters))
c2.metric("Visible wallets", len(nodes))
c3.metric("Visible flows", len(edges))
c4.metric("Suspicious wallets", len(suspicious_nodes))

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Selected Wallet Inspector")

import pandas as pd

def safe_flow_table(rows):
    df = pd.DataFrame(rows[:100])

    if df.empty:
        return df

    if "amount" in df.columns:
        df["amount"] = df["amount"].astype(str)

    return df.astype(str)


if selected:
    st.code(selected)
    incoming = [e for e in events if e.get("to") == selected]
    outgoing = [e for e in events if e.get("from") == selected]

    a, b, c = st.columns(3)
    a.metric("Incoming txs", len(incoming))
    b.metric("Outgoing txs", len(outgoing))
    c.metric(
        "Net flow",
        f"{sum(int(e.get('amount', 0)) for e in incoming) - sum(int(e.get('amount', 0)) for e in outgoing):,}"
    )

    st.markdown("### Incoming")
    st.dataframe(safe_flow_table(incoming), use_container_width=True)

    st.markdown("### Outgoing")
    st.dataframe(safe_flow_table(outgoing), use_container_width=True)

else:
    st.info("Click a node in the graph to inspect wallet flows.")

st.markdown("</div>", unsafe_allow_html=True)
