import gzip
import os
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import requests
from web3 import Web3

SCALE = 10**18

ZEROCHAIN_API = "https://2.api.explorer.cellframe.net/atoms/Backbone/zerochain/"

DATA_DIR = Path("data")
ETH_TRANSFERS = DATA_DIR / "eth_transfers.jsonl.gz"
BSC_TRANSFERS = DATA_DIR / "bsc_transfers.jsonl.gz"

OUT_CSV = Path("cf20_mint_crosscheck.csv")
OUT_JSON = Path("cf20_mint_crosscheck_summary.json")
CACHE_FILE = DATA_DIR / "block_timestamp_cache.json"

ETH_RPC = os.getenv("ETH_RPC", "")
BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")

# Known bridge/deposit wallets discovered in your ETH tracing.
# Add more confirmed deposit wallets here as you find them.
KNOWN_DEPOSIT_WALLETS = {
    "eth": {
        "0x4a831a8ebb160ad025d34a788c99e9320b9ab531",  # ETH bridge intake confirmed by user's tx
    },
    "bsc": {
        # Add confirmed BSC bridge/deposit wallet(s) here if discovered.
    },
}

# Matching settings
PAGES = int(os.getenv("ZEROCHAIN_PAGES", "300"))
LIMIT = int(os.getenv("ZEROCHAIN_LIMIT", "40"))
MATCH_WINDOW_HOURS = float(os.getenv("MATCH_WINDOW_HOURS", "72"))
AMOUNT_TOLERANCE_TOKENS = float(os.getenv("AMOUNT_TOLERANCE_TOKENS", "0"))
AMOUNT_TOLERANCE_RAW = int(AMOUNT_TOLERANCE_TOKENS * SCALE)

# If True, strict matches only use transfers into KNOWN_DEPOSIT_WALLETS.
# If False, it will compare mints against every transfer in the transfer files, which can create false positives.
ONLY_KNOWN_DEPOSIT_WALLETS = os.getenv("ONLY_KNOWN_DEPOSIT_WALLETS", "true").lower() != "false"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_cache(cache):
    DATA_DIR.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def get_w3(chain):
    if chain == "eth" and ETH_RPC:
        return Web3(Web3.HTTPProvider(ETH_RPC))
    if chain == "bsc" and BSC_RPC:
        return Web3(Web3.HTTPProvider(BSC_RPC))
    return None


def get_block_time(chain, block, cache, w3_by_chain):
    key = f"{chain}:{block}"
    if key in cache:
        return cache[key]

    w3 = w3_by_chain.get(chain)
    if w3 is None:
        return None

    try:
        b = w3.eth.get_block(int(block))
        ts = int(b["timestamp"])
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        cache[key] = dt
        return dt
    except Exception:
        return None


def fetch_zerochain_mints():
    rows = []

    for page in range(PAGES):
        offset = page * LIMIT

        try:
            r = requests.get(
                ZEROCHAIN_API,
                params={
                    "limit": LIMIT,
                    "offset": offset,
                    "reverse": "true",
                },
                timeout=20,
            )
            r.raise_for_status()
            payload = r.json()
        except Exception as e:
            print(f"Zerochain fetch stopped at page {page}: {e}")
            break

        items = payload.get("blocks_or_event", [])
        if not items:
            break

        for item in items:
            for datum in item.get("datums", []):
                if datum.get("type") != "DATUM_TOKEN_EMISSION":
                    continue

                d = datum.get("data", {})
                raw = int(d.get("value", 0))

                validators = d.get("valid_sign_hashes", []) or [
                    s.get("pkey_hash")
                    for s in d.get("data", [])
                    if isinstance(s, dict) and s.get("pkey_hash")
                ]

                rows.append({
                    "mint_time": datum.get("created"),
                    "token": d.get("ticker", "UNKNOWN"),
                    "amount_raw": raw,
                    "amount_tokens": raw / SCALE,
                    "mint_to": d.get("address", ""),
                    "datum_hash": datum.get("hash", ""),
                    "atom_hash": datum.get("atom_hash", ""),
                    "validator_count": len(validators),
                    "validators": validators,
                })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["mint_time"] = pd.to_datetime(df["mint_time"], errors="coerce", utc=True)
        df = df.dropna(subset=["mint_time"])
        df = df.sort_values("mint_time").reset_index(drop=True)

    return df


def load_transfers():
    frames = []
    cache = load_cache()
    w3_by_chain = {
        "eth": get_w3("eth"),
        "bsc": get_w3("bsc"),
    }

    for chain, path in [("eth", ETH_TRANSFERS), ("bsc", BSC_TRANSFERS)]:
        if not path.exists():
            print(f"Missing {path}; skipping {chain.upper()}")
            continue

        rows = []

        known = KNOWN_DEPOSIT_WALLETS.get(chain, set())

        with path.open() as f:
            for line in f:
                try:
                    tx = json.loads(line)
                    frm = str(tx.get("from", "")).lower()
                    to = str(tx.get("to", "")).lower()
                    amount_raw = int(tx.get("amount", 0))

                    if ONLY_KNOWN_DEPOSIT_WALLETS:
                        if known and to not in known:
                            continue
                        if not known:
                            # No confirmed bridge/deposit wallets for this chain yet.
                            continue

                    block = int(tx.get("block", 0))
                    t = tx.get("time") or tx.get("timestamp")

                    if not t and block:
                        t = get_block_time(chain, block, cache, w3_by_chain)

                    rows.append({
                        "chain": chain,
                        "transfer_time": t,
                        "block": block,
                        "tx_hash": tx.get("tx_hash", ""),
                        "from": frm,
                        "to": to,
                        "amount_raw": amount_raw,
                        "amount_tokens": amount_raw / SCALE,
                        "known_deposit_wallet": to in known,
                    })

                except Exception:
                    continue

        if rows:
            frame = pd.DataFrame(rows)
            frame["transfer_time"] = pd.to_datetime(frame["transfer_time"], errors="coerce", utc=True)
            frames.append(frame)

    save_cache(cache)

    if not frames:
        return pd.DataFrame(columns=[
            "chain", "transfer_time", "block", "tx_hash", "from", "to",
            "amount_raw", "amount_tokens", "known_deposit_wallet"
        ])

    df = pd.concat(frames, ignore_index=True)
    return df


def match_mints_to_transfers(mints, transfers):
    results = []

    if mints.empty:
        return pd.DataFrame()

    transfers_with_time = transfers.dropna(subset=["transfer_time"]).copy()
    transfers_without_time = transfers[transfers["transfer_time"].isna()].copy()

    window = pd.Timedelta(hours=MATCH_WINDOW_HOURS)

    for _, mint in mints.iterrows():
        mint_time = mint["mint_time"]
        amount_raw = int(mint["amount_raw"])

        candidates = pd.DataFrame()

        if not transfers_with_time.empty:
            candidates = transfers_with_time[
                (transfers_with_time["amount_raw"].sub(amount_raw).abs() <= AMOUNT_TOLERANCE_RAW)
                & (transfers_with_time["transfer_time"] <= mint_time)
                & ((mint_time - transfers_with_time["transfer_time"]) <= window)
            ].copy()

            if not candidates.empty:
                candidates["time_delta_minutes"] = (mint_time - candidates["transfer_time"]).dt.total_seconds() / 60
                candidates["amount_delta_tokens"] = (candidates["amount_raw"] - amount_raw) / SCALE
                candidates = candidates.sort_values(["time_delta_minutes", "amount_delta_tokens"], ascending=[True, True])

        # Fallback: amount-only if block timestamps could not be fetched.
        amount_only_candidates = pd.DataFrame()
        if candidates.empty and not transfers_without_time.empty:
            amount_only_candidates = transfers_without_time[
                transfers_without_time["amount_raw"].sub(amount_raw).abs() <= AMOUNT_TOLERANCE_RAW
            ].copy()

        if not candidates.empty:
            best = candidates.iloc[0]
            status = "matched_time_amount"
            candidate_count = len(candidates)
            matched_chain = best["chain"]
            matched_tx_hash = best["tx_hash"]
            matched_time = best["transfer_time"]
            matched_from = best["from"]
            matched_to = best["to"]
            time_delta_minutes = best["time_delta_minutes"]
            amount_delta_tokens = best["amount_delta_tokens"]

        elif not amount_only_candidates.empty:
            best = amount_only_candidates.iloc[0]
            status = "matched_amount_only_no_timestamp"
            candidate_count = len(amount_only_candidates)
            matched_chain = best["chain"]
            matched_tx_hash = best["tx_hash"]
            matched_time = ""
            matched_from = best["from"]
            matched_to = best["to"]
            time_delta_minutes = ""
            amount_delta_tokens = (int(best["amount_raw"]) - amount_raw) / SCALE

        else:
            status = "unmatched"
            candidate_count = 0
            matched_chain = ""
            matched_tx_hash = ""
            matched_time = ""
            matched_from = ""
            matched_to = ""
            time_delta_minutes = ""
            amount_delta_tokens = ""

        results.append({
            "mint_time": mint_time,
            "token": mint.get("token", ""),
            "mint_amount_tokens": mint["amount_tokens"],
            "mint_amount_raw": str(mint["amount_raw"]),
            "mint_to": mint.get("mint_to", ""),
            "datum_hash": mint.get("datum_hash", ""),
            "atom_hash": mint.get("atom_hash", ""),
            "validator_count": mint.get("validator_count", 0),
            "match_status": status,
            "candidate_count": candidate_count,
            "matched_chain": matched_chain,
            "matched_tx_hash": matched_tx_hash,
            "matched_time": matched_time,
            "matched_from": matched_from,
            "matched_to": matched_to,
            "time_delta_minutes": time_delta_minutes,
            "amount_delta_tokens": amount_delta_tokens,
        })

    return pd.DataFrame(results)


def main():
    print("\n==============================")
    print("CF20 MINT CROSS-CHECK")
    print("==============================\n")

    print("Fetching Zerochain emissions...")
    mints = fetch_zerochain_mints()
    print(f"Mint events loaded: {len(mints):,}")

    print("Loading bridge/deposit transfers...")
    transfers = load_transfers()
    print(f"Candidate transfers loaded: {len(transfers):,}")

    print("Matching mints against observed deposits...")
    result = match_mints_to_transfers(mints, transfers)

    if result.empty:
        print("No results.")
        return

    result.to_csv(OUT_CSV, index=False)

    total_minted = result["mint_amount_tokens"].sum()
    matched = result[result["match_status"].str.startswith("matched")]
    strict = result[result["match_status"] == "matched_time_amount"]
    unmatched = result[result["match_status"] == "unmatched"]

    matched_amount = matched["mint_amount_tokens"].sum()
    strict_amount = strict["mint_amount_tokens"].sum()
    unmatched_amount = unmatched["mint_amount_tokens"].sum()

    summary = {
        "generated_at": utc_now(),
        "settings": {
            "pages": PAGES,
            "limit": LIMIT,
            "match_window_hours": MATCH_WINDOW_HOURS,
            "amount_tolerance_tokens": AMOUNT_TOLERANCE_TOKENS,
            "only_known_deposit_wallets": ONLY_KNOWN_DEPOSIT_WALLETS,
            "known_deposit_wallets": {k: sorted(list(v)) for k, v in KNOWN_DEPOSIT_WALLETS.items()},
        },
        "mint_events": int(len(result)),
        "total_minted_tokens": float(total_minted),
        "matched_events_any": int(len(matched)),
        "matched_events_strict": int(len(strict)),
        "unmatched_events": int(len(unmatched)),
        "matched_amount_tokens_any": float(matched_amount),
        "matched_amount_tokens_strict": float(strict_amount),
        "unmatched_amount_tokens": float(unmatched_amount),
        "matched_amount_percent_any": float((matched_amount / total_minted) * 100) if total_minted else 0,
        "matched_amount_percent_strict": float((strict_amount / total_minted) * 100) if total_minted else 0,
        "unmatched_amount_percent": float((unmatched_amount / total_minted) * 100) if total_minted else 0,
    }

    OUT_JSON.write_text(json.dumps(summary, indent=2))

    print("\n==============================")
    print("RESULT")
    print("==============================\n")

    print(f"Total minted scanned:         {total_minted:,.2f} CF20")
    print(f"Strict matched amount:        {strict_amount:,.2f} CF20 ({summary['matched_amount_percent_strict']:.2f}%)")
    print(f"Any matched amount:           {matched_amount:,.2f} CF20 ({summary['matched_amount_percent_any']:.2f}%)")
    print(f"Unmatched amount:             {unmatched_amount:,.2f} CF20 ({summary['unmatched_amount_percent']:.2f}%)")
    print(f"Mint events:                  {len(result):,}")
    print(f"Strict matched events:        {len(strict):,}")
    print(f"Unmatched events:             {len(unmatched):,}")

    print(f"\nSaved: {OUT_CSV}")
    print(f"Saved: {OUT_JSON}")

    if not unmatched.empty:
        print("\nTop unmatched mint events:")
        print(
            unmatched.sort_values("mint_amount_tokens", ascending=False)
            .head(20)[["mint_time", "token", "mint_amount_tokens", "mint_to", "datum_hash"]]
            .to_string(index=False)
        )

    print("\nNotes:")
    print("- Strict matched = same amount, observed deposit before mint, within time window.")
    print("- Unmatched means no matching observed deposit in your current ETH/BSC data and known deposit-wallet list.")
    print("- This does not prove no backing exists elsewhere; it proves no match was found in the loaded public data.")


if __name__ == "__main__":
    main()
