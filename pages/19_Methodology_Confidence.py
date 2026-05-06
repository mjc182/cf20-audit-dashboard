import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Methodology & Confidence | CF20 Audit",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧪 Methodology & Confidence")
st.caption("Definitions, confidence levels, and audit-safe interpretation rules used throughout the dashboard.")

st.info(
    "This audit separates observed on-chain facts from interpretations. "
    "It avoids treating route exposure as exact sale proceeds, and it avoids treating unreconciled emissions as automatically illegal, lost, or sold."
)

st.markdown("## Core Definitions")

definitions = pd.DataFrame([
    {
        "Term": "Unreconciled CELL emissions",
        "Meaning": "Deduped CELL emission events not yet matched to indexed bridge/reserve evidence.",
        "Not the same as": "Proven theft, proven sale, proven illegal issuance, or final loss amount.",
    },
    {
        "Term": "Route exposure",
        "Meaning": "A graph path from the bridge-linked cluster into a known endpoint such as CEX, DEX/router, LP/pool, or MEV/searcher infrastructure.",
        "Not the same as": "Exact sale proceeds or exact final executed swap amount.",
    },
    {
        "Term": "CEX custody route",
        "Meaning": "A route that terminates at a labelled centralized exchange custody/deposit wallet.",
        "Not the same as": "Visible proof of internal exchange sale, because CEX trades are off-chain.",
    },
    {
        "Term": "DEX/router route",
        "Meaning": "A route that terminates at known swap/router/settlement infrastructure.",
        "Not the same as": "Exact swap output until transaction logs are decoded and verified.",
    },
    {
        "Term": "Bridge infrastructure identified",
        "Meaning": "Addresses with bridge-facing methods, bridge labels, Lock Token / Unlock Token behavior, or routing links to known bridge wallets.",
        "Not the same as": "Full reserve/backing reconciliation.",
    },
])

st.dataframe(definitions, use_container_width=True, hide_index=True)

st.markdown("## Confidence Levels")

confidence = pd.DataFrame([
    {
        "Level": "Observed",
        "Use when": "Directly visible in transaction data, contract method labels, token transfer logs, or local CSV outputs.",
        "Dashboard wording": "identified / observed / recorded",
    },
    {
        "Level": "Supported",
        "Use when": "Multiple on-chain signals point to the same interpretation.",
        "Dashboard wording": "strongly supported / classified as",
    },
    {
        "Level": "Inferred",
        "Use when": "The pattern suggests a role, but label/source confirmation is incomplete.",
        "Dashboard wording": "likely / candidate / probable",
    },
    {
        "Level": "Unresolved",
        "Use when": "The data identifies a gap or route but cannot prove the final state.",
        "Dashboard wording": "unresolved / not directly visible / requires further verification",
    },
])

st.dataframe(confidence, use_container_width=True, hide_index=True)

st.markdown("## Current Claims Matrix")

claims = pd.DataFrame([
    {
        "Claim": "Bridge lock/unlock infrastructure has been identified.",
        "Confidence": "Supported",
        "Safe wording": "Bridge lock/unlock infrastructure identified.",
    },
    {
        "Claim": "Bridge intake/router has been identified.",
        "Confidence": "Supported",
        "Safe wording": "Bridge-facing intake/router identified.",
    },
    {
        "Claim": "The bridge cluster routes into CEX, DEX/router, and MEV infrastructure.",
        "Confidence": "Supported",
        "Safe wording": "Market-route exposure identified.",
    },
    {
        "Claim": "Exact final sale proceeds are known.",
        "Confidence": "Unresolved",
        "Safe wording": "Exact realized sale amount remains unresolved.",
    },
    {
        "Claim": "Full reserve backing has been proven.",
        "Confidence": "Unresolved",
        "Safe wording": "Full reserve/backing reconciliation remains unresolved.",
    },
    {
        "Claim": "15.75M CELL is automatically illegal/sold/lost.",
        "Confidence": "Not supported",
        "Safe wording": "15.75M CELL is a reconciliation target, not a final accusation.",
    },
])

st.dataframe(claims, use_container_width=True, hide_index=True)

st.markdown("## Recommended Dashboard Language")

st.code(
    """
Use:
- Unreconciled CELL emissions
- Deduped events requiring bridge/reserve reconciliation
- Route exposure
- Market-route exposure identified
- CEX custody route identified
- DEX/router route identified
- Exact realized sale amount remains unresolved
- Full reserve/backing reconciliation remains unresolved

Avoid:
- Proven sale
- Stolen amount
- Illegal amount
- They sold X
- No bridge contract exists
- Exact market dump amount
- Full backing disproven
""",
    language="text",
)

st.warning(
    "The strongest audit is the one that clearly separates what is observed, what is supported, what is inferred, and what remains unresolved."
)
