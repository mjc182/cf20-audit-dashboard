from pathlib import Path

TARGETS = [
    Path("app.py"),
    Path("pages/9_Bridge_Infrastructure.py"),
    Path("pages/15_Market_Route_Evidence.py"),
    Path("pages/17_Route_Graph_Explorer.py"),
    Path("pages/18_Public_Audit_Report.py"),
]

REPLACEMENTS = {
    "Deduped unmatched CELL": "Unreconciled CELL emissions",
    "Deduped unmatched CELL estimate": "Unreconciled CELL emission estimate",
    "Independent unmatched-emission estimate": "Deduped events not yet matched to indexed bridge/reserve evidence",
    "Unmatched CELL": "Unreconciled CELL",
    "unmatched CELL": "unreconciled CELL",
    "Missing CELL": "Unreconciled CELL",
    "missing CELL": "unreconciled CELL",
    "Proven market sale": "Market-route exposure",
    "sold on open market": "routed into market infrastructure",
    "Sold on open market": "Routed into market infrastructure",
    "final sale amount": "final realized sale amount",
    "sale amount": "realized sale amount",
    "exact sale volume": "exact realized sale volume",
    "No bridge address found": "Bridge infrastructure now identified",
    "no bridge address found": "bridge infrastructure now identified",
    "final reserve/lock wallet": "final reserve/backing endpoint",
    "reserve wallet": "reserve/backing wallet",
    "This proves market-route exposure": "This supports market-route exposure",
    "proves exchange routing": "supports exchange-custody routing",
    "prove full reserve backing": "verify full reserve backing",
    "proves full reserve backing": "verifies full reserve backing",
    "proves final sale": "verifies final realized sale",
}

FOOTER = '''
st.caption(
    "Audit wording note: route-exposure totals show graph paths into market infrastructure. "
    "They are not exact final sale amounts. Unreconciled emissions are reconciliation targets, "
    "not automatically proven losses or illegal issuance."
)
'''

def patch_file(path):
    if not path.exists():
        print(f"Skipping missing file: {path}")
        return

    backup = path.with_suffix(path.suffix + ".bak_audit_wording")
    if not backup.exists():
        backup.write_text(path.read_text())

    text = path.read_text()
    old_text = text

    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)

    if path.name == "app.py" and "Audit wording note: route-exposure totals show graph paths" not in text:
        text = text.rstrip() + "\n\n" + FOOTER + "\n"

    path.write_text(text)
    print(("Updated" if text != old_text else "No wording changes needed") + f": {path}")

def add_sidebar_link():
    app = Path("app.py")
    if not app.exists():
        return

    text = app.read_text()
    link = '("pages/19_Methodology_Confidence.py", "Methodology & Confidence"),'

    if link in text:
        print("Methodology sidebar link already exists.")
        return

    anchors = [
        '("pages/18_Public_Audit_Report.py", "Public Audit Report"),',
        '("pages/17_Route_Graph_Explorer.py", "Route Graph Explorer"),',
        '("pages/7_Assumptions_Limitations.py", "Assumptions & Limitations"),',
    ]

    for anchor in anchors:
        if anchor in text:
            text = text.replace(anchor, anchor + "\n        " + link)
            app.write_text(text)
            print("Added Methodology & Confidence page to sidebar.")
            return

    print("Could not auto-add sidebar link. Add manually inside page_links:")
    print(link)

def main():
    print("\n==============================")
    print("CF20 AUDIT WORDING POLISH PATCH")
    print("==============================\n")

    for path in TARGETS:
        patch_file(path)

    add_sidebar_link()

    print("\nDone. Re-run Streamlit.")

if __name__ == "__main__":
    main()
