from pathlib import Path

APP = Path("app.py")
if not APP.exists():
    raise FileNotFoundError("app.py not found. Run this from your repo root.")

text = APP.read_text()

if "Completed 35ce Bridge / Aggregator Trace" in text:
    print("35ce trace section already exists.")
    raise SystemExit

section = r'''
# ==============================
# 35CE BRIDGE / AGGREGATOR TRACE
# ==============================

trace_35ce = load_json(Path("auto_trace_35ce_summary.json"))
recipients_35ce = load_csv(Path("auto_trace_35ce_recipient_summary.csv"))

st.markdown('<a id="trace-35ce"></a>', unsafe_allow_html=True)

if trace_35ce:
    complete_35ce = trace_35ce.get("complete_trace_result", {})
    final_balance_35ce = complete_35ce.get("final_balance_cell", trace_35ce.get("current_balance_cell", 0))

    st.markdown(
        f"""
<div class="section">
  <div class="section-title">
    <div>
      <h2>Completed 35ce Bridge / Aggregator Trace</h2>
      <p>The 0x35ce address was previously identified as a bridge / aggregator address. The BSC trace now shows it behaved as a pass-through distribution node and ended at zero balance.</p>
    </div>
    <div class="badge">Trace complete</div>
  </div>

  <div class="kpi-grid" style="grid-template-columns:repeat(5,1fr);">
    <div class="kpi-card tone-blue">
      <div class="kpi-label">Target wallet</div>
      <div class="kpi-value" style="font-size:1.05rem;">0x35ce...e60</div>
      <div class="kpi-sub">Bridge / aggregator address</div>
    </div>
    <div class="kpi-card tone-green">
      <div class="kpi-label">Final balance</div>
      <div class="kpi-value">{compact(final_balance_35ce)} CELL</div>
      <div class="kpi-sub">Trace reached zero balance</div>
    </div>
    <div class="kpi-card tone-orange">
      <div class="kpi-label">Total outbound</div>
      <div class="kpi-value">{compact(complete_35ce.get("total_outbound_cell", 0))}</div>
      <div class="kpi-sub">CELL routed onward during trace</div>
    </div>
    <div class="kpi-card tone-purple">
      <div class="kpi-label">Unique recipients</div>
      <div class="kpi-value">{complete_35ce.get("unique_recipients", "—")}</div>
      <div class="kpi-sub">Downstream recipients in trace</div>
    </div>
    <div class="kpi-card tone-blue">
      <div class="kpi-label">Outbound events</div>
      <div class="kpi-value">{complete_35ce.get("outbound_events", "—")}</div>
      <div class="kpi-sub">Outbound transfer events</div>
    </div>
  </div>

  <br>

  <div class="success-note">
    <b>Audit finding:</b> The <code>0x35ce...</code> bridge / aggregator address was traced to zero balance.
    Its largest traced output was <b>552,542.49 CELL</b> to <code>0xa2c1...</code>, and it also routed <b>103,911 CELL</b> to <code>0xda8a...</code>.
  </div>

  <br>

  <div class="note">
    <b>Reserve/backing implication:</b> In this BSC trace, <code>0x35ce...</code> behaved as a pass-through / distribution node, not as a reserve endpoint.
    This strengthens the conclusion that current verified reserve/backing candidates do not yet reconcile the BSC supply.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    if not recipients_35ce.empty:
        show = recipients_35ce.copy()

        if "amount_cell" in show.columns:
            show["amount_cell_num"] = pd.to_numeric(show["amount_cell"], errors="coerce").fillna(0)
            show = show.sort_values("amount_cell_num", ascending=False)
            show["amount_cell"] = show["amount_cell_num"].map(lambda x: f"{x:,.8f}")
            show = show.drop(columns=["amount_cell_num"], errors="ignore")

        if "share_of_total_out_percent" in show.columns:
            show["share_of_total_out_percent"] = (
                pd.to_numeric(show["share_of_total_out_percent"], errors="coerce")
                .fillna(0)
                .map(lambda x: f"{x:,.2f}%")
            )

        st.markdown("### Top Recipients from Completed 35ce Trace")
        st.dataframe(show.head(20), use_container_width=True, hide_index=True)

else:
    st.markdown(
        """
<div class="section">
  <div class="section-title">
    <div>
      <h2>35ce Bridge / Aggregator Trace</h2>
      <p>Run the 35ce auto-trace to generate <code>auto_trace_35ce_summary.json</code>.</p>
    </div>
    <div class="badge orange">Pending trace output</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
'''

markers = [
    "# ==============================\n# RESERVE / BACKING RECONCILIATION\n# ==============================",
    "# ==============================\n# EXPOSURE + STATUS\n# ==============================",
]

inserted = False
for marker in markers:
    if marker in text:
        text = text.replace(marker, section + "\n\n" + marker)
        inserted = True
        break

if not inserted:
    text += "\n\n" + section

# Add nav link if nav exists.
text = text.replace(
    '<a href="#trace-8bbf">8bbf Trace</a>',
    '<a href="#trace-8bbf">8bbf Trace</a>\n    <a href="#trace-35ce">35ce Trace</a>'
)

text = text.replace(
    '<a href="#central-wallet-traces">Central Traces</a>',
    '<a href="#central-wallet-traces">Central Traces</a>\n    <a href="#trace-35ce">35ce Trace</a>'
)

APP.write_text(text)
print("Added completed 35ce bridge / aggregator trace section to app.py.")
