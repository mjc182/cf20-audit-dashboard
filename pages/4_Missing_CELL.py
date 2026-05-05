import json
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
st.set_page_config(page_title="Missing CELL", page_icon="⚠", layout="wide")
st.title("⚠ Missing CELL / mCELL")
W=Path("missing_cell_wallets.csv"); E=Path("missing_cell_events.csv"); S=Path("missing_cell_summary.json")
if not W.exists() or not E.exists(): st.info("Run `filter_missing_cell_only.py` and upload missing CELL outputs."); st.stop()
wallets=pd.read_csv(W); events=pd.read_csv(E); summary=json.loads(S.read_text()) if S.exists() else {}
c1,c2,c3,c4=st.columns(4); c1.metric("Missing CELL",f"{float(summary.get('missing_cell',pd.to_numeric(wallets.get('missing_cell',pd.Series(dtype=float)),errors='coerce').sum())):,.2f}"); c2.metric("Missing %",f"{float(summary.get('missing_percent',0)):,.2f}%"); c3.metric("Recipient wallets",f"{int(summary.get('recipient_count',len(wallets))):,}"); c4.metric("Missing events",f"{int(summary.get('missing_events',len(events))):,}")
st.markdown("### Top recipient wallets"); st.dataframe(wallets.head(100),use_container_width=True,hide_index=True)
if {"mint_to","missing_cell"}.issubset(wallets.columns):
    c=wallets.head(20).copy(); c["missing_cell"]=pd.to_numeric(c["missing_cell"],errors="coerce"); c["wallet_short"]=c["mint_to"].astype(str).str[:10]+"..."+c["mint_to"].astype(str).str[-6:]
    st.altair_chart(alt.Chart(c).mark_bar().encode(x=alt.X("missing_cell:Q",title="Missing CELL"),y=alt.Y("wallet_short:N",sort="-x",title=None),tooltip=["mint_to:N",alt.Tooltip("missing_cell:Q",format=",.2f")]).properties(height=520),use_container_width=True)
st.markdown("### Largest unmatched CELL mint events"); 
if "mint_amount_tokens" in events.columns: events["mint_amount_tokens"]=pd.to_numeric(events["mint_amount_tokens"],errors="coerce"); events=events.sort_values("mint_amount_tokens",ascending=False)
st.dataframe(events.head(250),use_container_width=True,hide_index=True)
