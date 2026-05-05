import json
from pathlib import Path
import pandas as pd
import streamlit as st
st.set_page_config(page_title="Bridge-Out Trace", page_icon="⟲", layout="wide")
st.title("⟲ Bridge-Out Trace")
st.markdown("""
### Key bridge-out evidence
A `DATUM_TX` record links the largest unmatched recipient wallet to a bridge-out action:

- Source wallet: `Rj7J7...MLE7o7T`
- Action tags: `BRIDGE` · `OUT` · `BEP20`
- Destination: `0x1fa6348d9b13d316c62d54f62bea4e1a7207d9d6`
- Approximate bridge condition value: `3.876M CELL`
""")
RAW=Path("zerochain_missing_cell_activity_raw.csv"); SUMMARY=Path("zerochain_missing_cell_outflow_summary.csv"); SJ=Path("zerochain_missing_cell_outflow_summary.json"); EDGES=Path("zerochain_missing_cell_outgoing_edges.csv")
s=json.loads(SJ.read_text()) if SJ.exists() else {}
c1,c2,c3=st.columns(3); c1.metric("Raw activity hits",f"{int(s.get('raw_hits',0)):,}"); c2.metric("Outgoing edge rows",f"{int(s.get('outgoing_edges',0)):,}"); c3.metric("Targets scanned",f"{int(s.get('targets_scanned',0)):,}")
if SUMMARY.exists(): st.markdown("### Outflow summary"); st.dataframe(pd.read_csv(SUMMARY),use_container_width=True,hide_index=True)
else: st.info("No outflow summary CSV found. Run `trace_missing_cell_outflows.py`.")
if EDGES.exists(): st.markdown("### Outgoing edges"); st.dataframe(pd.read_csv(EDGES),use_container_width=True,hide_index=True)
if RAW.exists(): st.markdown("### Raw activity sample"); st.dataframe(pd.read_csv(RAW).head(200),use_container_width=True,hide_index=True)
