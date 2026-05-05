import json
from pathlib import Path
import pandas as pd
import streamlit as st
st.set_page_config(page_title="Verified Wallets", page_icon="☷", layout="wide")
st.title("☷ Verified Wallets")
BALANCES=Path("verified_wallet_balances.json"); REGISTRY=Path("verified_wallets.json")
if REGISTRY.exists():
    with st.expander("Verified wallet registry", expanded=False):
        try: st.json(json.loads(REGISTRY.read_text()))
        except Exception: st.warning("Could not parse verified_wallets.json")
if not BALANCES.exists(): st.info("Run `track_verified_wallets.py` and upload `verified_wallet_balances.json`."); st.stop()
df=pd.DataFrame(json.loads(BALANCES.read_text()))
c1,c2,c3=st.columns(3); c1.metric("Tracked wallets",f"{len(df):,}"); c2.metric("Tracked balance",f"{pd.to_numeric(df['balance_tokens'],errors='coerce').sum():,.2f}"); c3.metric("Tracked supply %",f"{pd.to_numeric(df['supply_percent'],errors='coerce').sum():,.4f}%")
st.dataframe(df,use_container_width=True,hide_index=True)
st.markdown("### Category Totals"); totals=df.groupby(["chain","group"],as_index=False).agg(balance_tokens=("balance_tokens","sum"),supply_percent=("supply_percent","sum")); st.dataframe(totals,use_container_width=True,hide_index=True)
