from pathlib import Path
import streamlit as st
st.set_page_config(page_title="Evidence Downloads", page_icon="◈", layout="wide")
st.title("◈ Evidence Downloads")
evidence_files=[("Verified Wallet Registry","verified_wallets.json"),("Verified Wallet Balances","verified_wallet_balances.json"),("Mint Cross-Check","cf20_mint_crosscheck.csv"),("Mint Cross-Check Summary","cf20_mint_crosscheck_summary.json"),("Missing CELL Wallets","missing_cell_wallets.csv"),("Missing CELL Events","missing_cell_events.csv"),("Missing CELL Summary","missing_cell_summary.json"),("Zerochain Outflow Raw","zerochain_missing_cell_activity_raw.csv"),("Zerochain Outflow Edges","zerochain_missing_cell_outgoing_edges.csv"),("Zerochain Outflow Summary","zerochain_missing_cell_outflow_summary.csv"),("BSC Target Direct Transfers","bsc_target_direct_transfers.csv"),("BSC Target Market Routes","bsc_target_market_routes.csv")]
cols=st.columns(3)
for i,(label,filename) in enumerate(evidence_files):
    p=Path(filename)
    with cols[i%3]:
        if p.exists(): st.download_button(f"Download {label}",p.read_bytes(),file_name=filename,mime="text/csv" if filename.endswith(".csv") else "application/json",use_container_width=True)
        else: st.caption(f"Missing: {filename}")
