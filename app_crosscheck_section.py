# ===============================
# 🔁 CF20 MINT CROSS-CHECK SECTION
# ===============================

def load_mint_crosscheck():
    path = Path("cf20_mint_crosscheck.csv")
    summary_path = Path("cf20_mint_crosscheck_summary.json")

    rows = pd.DataFrame()
    summary = {}

    if path.exists():
        rows = pd.read_csv(path)

    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text())
        except Exception:
            summary = {}

    return rows, summary


st.markdown("## 🔁 CF20 Mint Cross-Check")

cross_df, cross_summary = load_mint_crosscheck()

if cross_df.empty:
    st.info("No CF20 mint cross-check data found. Run cross_check_cf20_mints.py first and commit the output CSV/JSON.")
else:
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Mint Events Checked", f"{int(cross_summary.get('mint_events', len(cross_df))):,}")
    c2.metric("Total Minted Scanned", f"{float(cross_summary.get('total_minted_tokens', cross_df['mint_amount_tokens'].sum())):,.2f}")
    c3.metric("Strict Match %", f"{float(cross_summary.get('matched_amount_percent_strict', 0)):,.2f}%")
    c4.metric("Unmatched %", f"{float(cross_summary.get('unmatched_amount_percent', 0)):,.2f}%")

    status_counts = cross_df["match_status"].value_counts().reset_index()
    status_counts.columns = ["match_status", "events"]

    chart = alt.Chart(status_counts).mark_arc(innerRadius=55).encode(
        theta="events:Q",
        color=alt.Color("match_status:N", legend=alt.Legend(orient="bottom")),
        tooltip=["match_status:N", "events:Q"],
    ).properties(height=260)

    st.altair_chart(chart, use_container_width=True)

    st.markdown("### Largest Unmatched Mints")

    unmatched = cross_df[cross_df["match_status"] == "unmatched"].copy()

    if unmatched.empty:
        st.success("All scanned mint events found a matching observed deposit under current rules.")
    else:
        unmatched = unmatched.sort_values("mint_amount_tokens", ascending=False).head(25)
        unmatched["mint_amount_tokens"] = unmatched["mint_amount_tokens"].apply(lambda x: f"{float(x):,.2f}")

        st.dataframe(
            unmatched[[
                "mint_time",
                "token",
                "mint_amount_tokens",
                "mint_to",
                "datum_hash",
                "validator_count",
            ]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Full Cross-Check Results")
    show_cross = cross_df.copy().head(500)
    show_cross["mint_amount_tokens"] = show_cross["mint_amount_tokens"].apply(lambda x: f"{float(x):,.2f}")
    st.dataframe(show_cross, use_container_width=True, hide_index=True)
