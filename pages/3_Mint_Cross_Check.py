import json
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
st.set_page_config(page_title="Mint Cross-Check", page_icon="⇄", layout="wide")
st.title("⇄ Mint Cross-Check")
CSV=Path("cf20_mint_crosscheck.csv"); SUMMARY=Path("cf20_mint_crosscheck_summary.json")
if not CSV.exists(): st.info("Run `cross_check_cf20_mints.py` and upload `cf20_mint_crosscheck.csv`."); st.stop()
df=pd.read_csv(CSV); summary=json.loads(SUMMARY.read_text()) if SUMMARY.exists() else {}
c1,c2,c3,c4=st.columns(4); c1.metric("Mint events checked",f"{int(summary.get('mint_events',len(df))):,}"); c2.metric("Total minted scanned",f"{float(summary.get('total_minted_tokens',0)):,.2f}"); c3.metric("Matched amount",f"{float(summary.get('matched_amount_tokens',0)):,.2f}"); c4.metric("Unmatched amount",f"{float(summary.get('unmatched_amount_tokens',0)):,.2f}")
if "match_status" in df.columns:
    counts=df["match_status"].value_counts().reset_index(); counts.columns=["match_status","events"]
    st.altair_chart(alt.Chart(counts).mark_arc(innerRadius=60).encode(theta="events:Q",color=alt.Color("match_status:N",legend=alt.Legend(orient="bottom")),tooltip=["match_status:N","events:Q"]).properties(height=300),use_container_width=True)
st.markdown("### Largest unmatched events")
unmatched=df[df.get("match_status","").eq("unmatched")].copy() if "match_status" in df.columns else df.copy()
if "mint_amount_tokens" in unmatched.columns: unmatched["mint_amount_tokens"]=pd.to_numeric(unmatched["mint_amount_tokens"],errors="coerce"); unmatched=unmatched.sort_values("mint_amount_tokens",ascending=False)
st.dataframe(unmatched.head(100),use_container_width=True,hide_index=True)
st.markdown("### Full Results"); st.dataframe(df.head(1000),use_container_width=True,hide_index=True)
