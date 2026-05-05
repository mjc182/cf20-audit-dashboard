import streamlit as st

st.set_page_config(page_title="Assumptions & Limitations", page_icon="📌", layout="wide")

st.title("📌 Assumptions & Limitations")

st.markdown(
    """
## Unit convention

Throughout this dashboard:

```text
1 mCELL = 1,000 CELL
```

Therefore:

```text
1,295 mCELL = 1,295,000 CELL-equivalent
15.8M–16.0M CELL = 15,800–16,000 mCELL-equivalent
```

## What is proven

- Unmatched CELL/mCELL emissions were identified from Zerochain emission data.
- Deduplication is performed by `datum_hash` where available.
- The top unmatched recipient wallets are highly concentrated.
- A `DATUM_TX` record links the largest unmatched recipient to a `BRIDGE OUT BEP20` transaction.

## What is not yet proven

- The exact amount sold on open markets.
- Whether the BEP20 destination wallet sold to an exchange, DEX pool, market maker, or OTC recipient.
- The full identity of each wallet controller.
- Whether every unmatched emission is illegal rather than unresolved due to missing deposit-wallet coverage.

## Matching limitations

Known wallet matching may be incomplete. Current matching depends on the wallet registry available in:

```text
verified_wallets.json
```

The audit separates:

```text
official disclosure
independent unmatched emissions
bridge-out evidence
market-sale quantification
```

These should not be merged into a single claim unless additional evidence supports it.

## Evidence handling

Each evidence file can be hashed with:

```text
build_audit_master_summary.py
```

The generated hashes are written to:

```text
evidence_hashes.json
evidence_hashes.csv
```
"""
)
