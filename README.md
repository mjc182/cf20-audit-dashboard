# CF20 Public Audit Dashboard

Independent, open-source dashboard for analyzing CF20 token emissions, validator authorization, wallet clusters, and suspicious flow behavior using publicly available blockchain data.

## Features

- Zerochain `DATUM_TOKEN_EMISSION` extraction
- Validator signature concentration analysis
- Wallet labeling and supply concentration view
- Interactive graph visualization
- Cluster highlighting
- Suspicious flow detection
- Optional ETH/BSC burn scan via RPC secrets

## Project structure

```text
cf20-audit-dashboard/
├── app.py
├── requirements.txt
├── pages/
│   └── 4_Graph.py
└── .streamlit/
    └── config.toml
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud secrets

Do **not** commit API keys to GitHub. Add these in Streamlit Cloud app settings:

```toml
ETH_RPC="https://mainnet.infura.io/v3/YOUR_KEY"
BSC_RPC="https://bsc-dataseed.binance.org/"
```

## Deploy

1. Create a public GitHub repo named `cf20-audit-dashboard`
2. Upload this project
3. Go to Streamlit Community Cloud
4. Create a new app from the repo
5. Main file: `app.py`
6. Add secrets
7. Deploy

## Methodology

- Mint records are extracted from Zerochain explorer API atom records.
- Validator control is inferred from emission signature hashes.
- Wallet labels and suspicious flow detection are heuristic.
- ETH/BSC backing checks require RPC data and are optional.

## Limitations

No direct cryptographic cross-chain source transaction reference was observed in the sample Zerochain emission data. This dashboard provides transparent, reproducible analysis from public data, but wallet labels and cross-chain confidence are not identity proof.
