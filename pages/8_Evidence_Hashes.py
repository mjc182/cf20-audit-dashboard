import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Evidence Hashes", page_icon="🔐", layout="wide")

HASHES_CSV = Path("evidence_hashes.csv")
HASHES_JSON = Path("evidence_hashes.json")

st.title("🔐 Evidence Hashes")
st.caption("SHA256 hashes for CSV/JSON audit artifacts. Use these to verify evidence integrity.")

if HASHES_CSV.exists():
    df = pd.read_csv(HASHES_CSV)
    st.dataframe(df, use_container_width=True, hide_index=True)
elif HASHES_JSON.exists():
    try:
        df = pd.DataFrame(json.loads(HASHES_JSON.read_text()))
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Could not parse evidence_hashes.json: {e}")
else:
    st.info("No evidence hashes found. Run `python3 build_audit_master_summary.py`.")
