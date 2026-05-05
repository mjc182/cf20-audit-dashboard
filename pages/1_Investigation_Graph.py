import gzip, json, math
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Investigation Graph", page_icon="☍", layout="wide")
DATA_DIR=Path("data"); ETH_GZ=DATA_DIR/"eth_transfers.jsonl.gz"; ETH_JSONL=DATA_DIR/"eth_transfers.jsonl"; SCALE=10**18
KNOWN={"0x4a831a8ebb160ad025d34a788c99e9320b9ab531":("Bridge Intake","Bridge"),"0x35ce1677d3d6aaaacd96510704d3c8617a12ee60":("Aggregator L1","Bridge"),"0x50ebb0827aa80ba1a2a30b38581629996262d481":("Aggregator L2","Bridge"),"0x52105eee8e836ff9e60cb02c0a665cbe2fc3a30d":("Secondary Distributor","Bridge"),"0x9c4cc862f51b1ba90485de3502aa058ca4331f32":("Router / Exchange-like","Router")}
def data_file():
    if ETH_GZ.exists(): return ETH_GZ
    if ETH_JSONL.exists(): return ETH_JSONL
    return None
@st.cache_data(show_spinner=False)
def load(path_str,max_rows=250000):
    path=Path(path_str); opener=gzip.open if path.suffix==".gz" else open; rows=[]
    with opener(path,"rt") as f:
        for i,line in enumerate(f):
            if i>=max_rows: break
            try:
                tx=json.loads(line); rows.append({"from":str(tx.get("from","")).lower(),"to":str(tx.get("to","")).lower(),"amount":int(tx.get("amount",0))/SCALE,"tx_hash":tx.get("tx_hash",""),"block":int(tx.get("block",0) or 0)})
            except Exception: pass
    return pd.DataFrame(rows)
def short(a): return str(a)[:6]+"..."+str(a)[-6:]
def label(a): return KNOWN.get(str(a).lower(),(short(a),"Wallet"))[0]
def group(a): return KNOWN.get(str(a).lower(),(short(a),"Wallet"))[1]
st.title("☍ Investigation Graph"); st.caption("Heavy transfer-data graph page.")
f=data_file()
if f is None: st.error("Missing `data/eth_transfers.jsonl.gz` or `data/eth_transfers.jsonl`."); st.stop()
df=load(str(f)); st.success(f"Loaded {len(df):,} transfers from `{f}`")
c1,c2,c3=st.columns([2,1,1])
with c1: wallet=st.text_input("Focus wallet", "0x4a831a8ebb160ad025d34a788c99e9320b9ab531").lower().strip()
with c2: min_amount=st.number_input("Minimum flow amount",0, value=1000, step=500)
with c3: max_edges=st.number_input("Max edges",10,300,120,10)
rel=df[(df["from"]==wallet)|(df["to"]==wallet)]
if rel.empty: st.warning("No transfers found for this wallet."); st.stop()
edges=rel.groupby(["from","to"],as_index=False).agg(amount=("amount","sum"),txs=("amount","count")).query("amount >= @min_amount").sort_values("amount",ascending=False).head(int(max_edges))
if edges.empty: st.warning("No edges matched filter."); st.stop()
nodes=sorted(set(edges["from"]).union(set(edges["to"])))
node_rows=[]
for i,n in enumerate(nodes):
    if n==wallet: x=y=0
    else:
        angle=2*math.pi*i/max(1,len(nodes)); radius=1+(i%7)*.09; x=radius*math.cos(angle); y=radius*math.sin(angle)
    node_rows.append({"wallet":n,"label":label(n),"group":group(n),"x":x,"y":y,"size":700 if n==wallet else 320})
node_df=pd.DataFrame(node_rows); pos={r.wallet:(r.x,r.y) for r in node_df.itertuples()}
lines=[]
for idx,row in edges.reset_index(drop=True).iterrows():
    sx,sy=pos[row["from"]]; tx,ty=pos[row["to"]]; risk="Large Flow" if row["amount"]>=edges["amount"].quantile(.9) else "Observed Flow"
    lines += [{"edge_id":idx,"x":sx,"y":sy,"from":row["from"],"to":row["to"],"amount":row["amount"],"txs":row["txs"],"risk":risk},{"edge_id":idx,"x":tx,"y":ty,"from":row["from"],"to":row["to"],"amount":row["amount"],"txs":row["txs"],"risk":risk}]
line_df=pd.DataFrame(lines)
edge_chart=alt.Chart(line_df).mark_line(opacity=.7).encode(x=alt.X("x:Q",axis=None),y=alt.Y("y:Q",axis=None),detail="edge_id:N",size=alt.Size("amount:Q",scale=alt.Scale(range=[.5,4]),legend=None),color=alt.Color("risk:N",scale=alt.Scale(range=["#64748b","#ef4444"])),tooltip=["from:N","to:N",alt.Tooltip("amount:Q",format=",.2f"),"txs:Q"])
node_chart=alt.Chart(node_df).mark_circle(stroke="#0f172a",strokeWidth=1.2).encode(x=alt.X("x:Q",axis=None),y=alt.Y("y:Q",axis=None),size=alt.Size("size:Q",legend=None),color=alt.Color("group:N",scale=alt.Scale(range=["#a855f7","#ef4444","#38bdf8"])),tooltip=["label:N","wallet:N","group:N"])
labels=alt.Chart(node_df[node_df["wallet"].eq(wallet)|node_df["group"].ne("Wallet")]).mark_text(dy=24,color="#cbd5e1",fontSize=10,fontWeight="bold").encode(x="x:Q",y="y:Q",text="label:N")
st.altair_chart((edge_chart+node_chart+labels).properties(height=650).configure_view(strokeWidth=0).interactive(),use_container_width=True)
st.markdown("### Direct Edges"); show=edges.copy(); show["from_label"]=show["from"].apply(label); show["to_label"]=show["to"].apply(label); show["amount"]=show["amount"].map(lambda x:f"{x:,.2f}"); st.dataframe(show[["from_label","to_label","from","to","amount","txs"]],use_container_width=True,hide_index=True)
