from pathlib import Path

APP = Path("app.py")
if not APP.exists():
    raise FileNotFoundError("app.py not found. Run this from your repo root.")

text = APP.read_text()

if "Old-CELL Bridge Claim Check" in text:
    print("Old-CELL claim check section already exists.")
    raise SystemExit

section = r'''
# ==============================
# OLD-CELL BRIDGE CLAIM CHECK
# ==============================

oldcell_c3b8 = load_json(Path("auto_trace_oldcell_c3b8_summary.json"))
oldcell_8929 = load_json(Path("auto_trace_oldcell_8929_summary.json"))
oldcell_child_summary = load_csv(Path("oldcell_458b_child_probe_summary.csv"))
oldcell_secondary_summary = load_csv(Path("oldcell_secondary_child_probe_summary.csv"))

st.markdown('<a id="oldcell-claim-check"></a>', unsafe_allow_html=True)

st.markdown(
    """
<div class="section">
  <div class="section-title">
    <div>
      <h2>Old-CELL Bridge Claim Check</h2>
      <p>A public claim alleged that 5M+ old CELL was bridged back and dumped on MEXC. The audit separates what is verified from what remains unproven.</p>
    </div>
    <div class="badge orange">Claim reviewed</div>
  </div>

  <div class="kpi-grid" style="grid-template-columns:repeat(4,1fr);">
    <div class="kpi-card tone-green">
      <div class="kpi-label">Bridge/unlock to 0xc3b8</div>
      <div class="kpi-value">5.21M</div>
      <div class="kpi-sub">5,207,505.2 old CELL routed into 0xc3b8</div>
    </div>
    <div class="kpi-card tone-blue">
      <div class="kpi-label">0xc3b8 old-CELL balance</div>
      <div class="kpi-value">0</div>
      <div class="kpi-sub">0xc3b8 old-CELL trace reached zero</div>
    </div>
    <div class="kpi-card tone-purple">
      <div class="kpi-label">Largest held branch</div>
      <div class="kpi-value">2.63M</div>
      <div class="kpi-sub">0xa9ad still held 2,625,551.2 old CELL at scan end</div>
    </div>
    <div class="kpi-card tone-orange">
      <div class="kpi-label">MEXC route found</div>
      <div class="kpi-value">No</div>
      <div class="kpi-sub">No MEXC-labelled endpoint found in traced paths so far</div>
    </div>
  </div>

  <br>

  <div class="success-note">
    <b>Verified:</b> The transaction claim that 5M+ old CELL was bridged/unlocked into <code>0xc3b8...</code> is supported.
    The old-CELL balance was then routed onward and <code>0xc3b8...</code> reached zero old-CELL balance.
  </div>

  <br>

  <div class="note">
    <b>Not proven:</b> The claim that these tokens were “dumped on MEXC” is not supported by the traced on-chain evidence so far.
    The reviewed paths route to downstream wallets, back to <code>0xe0ca...</code>, or remain held. No MEXC-labelled endpoint was identified in this trace set.
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

oldcell_claim_rows = [
    {
        "Claim component": "5M+ old CELL bridged/unlocked into 0xc3b8",
        "Audit status": "Supported",
        "Evidence": "Tx 0xb6bffa... and old-CELL trace show ~5.207M old CELL routed into 0xc3b8.",
    },
    {
        "Claim component": "0xc3b8 routed old CELL onward",
        "Audit status": "Verified",
        "Evidence": "0xc3b8 old-CELL trace reached zero, with outbound routes to 0x8929... and 0x0b88...",
    },
    {
        "Claim component": "Largest old-CELL branch went to MEXC",
        "Audit status": "Not supported so far",
        "Evidence": "0xa9ad... retained 2,625,551.2 old CELL with no further movement found through the scan end block.",
    },
    {
        "Claim component": "1M old-CELL branch dumped on MEXC",
        "Audit status": "Not supported so far",
        "Evidence": "0x458b... split 1M into ten 100k wallets. Several held balances; moved secondary-child outputs routed to 0xe0ca..., not a MEXC-labelled endpoint.",
    },
    {
        "Claim component": "Exchange sale / dump",
        "Audit status": "Unproven",
        "Evidence": "No traced path currently reaches a MEXC-labelled address. CEX-internal trading would require exchange records.",
    },
]

st.markdown("### Claim vs Evidence")
st.dataframe(pd.DataFrame(oldcell_claim_rows), use_container_width=True, hide_index=True)

st.markdown("### Old-CELL Route Summary")

oldcell_route_rows = [
    {
        "Route": "Bridge/unlock → 0xc3b8",
        "Amount": "5,207,505.2 old CELL",
        "Status": "Verified",
        "Interpretation": "Old-CELL bridge/unlock into known custody path.",
    },
    {
        "Route": "0xc3b8 → 0x8929",
        "Amount": "4,487,005.2 old CELL",
        "Status": "Verified",
        "Interpretation": "Largest downstream route from 0xc3b8.",
    },
    {
        "Route": "0x8929 → 0xa9ad",
        "Amount": "3,551,757.2 old CELL",
        "Status": "Partially resolved",
        "Interpretation": "0xa9ad retained 2,625,551.2 old CELL at scan end.",
    },
    {
        "Route": "0x8929 → 0x458b → ten 100k wallets",
        "Amount": "1,000,000 old CELL",
        "Status": "Verified split",
        "Interpretation": "Split into ten child wallets; no MEXC-labelled endpoint found in traced outputs.",
    },
    {
        "Route": "Secondary moved child outputs → 0xe0ca",
        "Amount": "308,180 old CELL",
        "Status": "Verified",
        "Interpretation": "Moved secondary-child outputs routed back to 0xe0ca, not MEXC.",
    },
]

st.dataframe(pd.DataFrame(oldcell_route_rows), use_container_width=True, hide_index=True)

if not oldcell_child_summary.empty:
    st.markdown("### Ten 100k Child Wallet Probe")
    show = oldcell_child_summary.copy()
    for col in ["current_balance_cell", "change_count", "event_count"]:
        if col in show.columns:
            show[col] = pd.to_numeric(show[col], errors="coerce")
    st.dataframe(show, use_container_width=True, hide_index=True)

if not oldcell_secondary_summary.empty:
    st.markdown("### Secondary Child Wallet Probe")
    show2 = oldcell_secondary_summary.copy()
    for col in ["current_balance_cell", "change_count", "event_count"]:
        if col in show2.columns:
            show2[col] = pd.to_numeric(show2[col], errors="coerce")
    st.dataframe(show2, use_container_width=True, hide_index=True)
'''

# Insert before reserve/backing if present, otherwise before exposure/status.
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

# Add nav link if navbar exists.
text = text.replace(
    '<a href="#trace-35ce">35ce Trace</a>',
    '<a href="#trace-35ce">35ce Trace</a>\n    <a href="#oldcell-claim-check">Old-CELL Claim</a>'
)

text = text.replace(
    '<a href="#trace-8bbf">8bbf Trace</a>',
    '<a href="#trace-8bbf">8bbf Trace</a>\n    <a href="#oldcell-claim-check">Old-CELL Claim</a>'
)

APP.write_text(text)
print("Added Old-CELL Bridge Claim Check section to app.py.")
