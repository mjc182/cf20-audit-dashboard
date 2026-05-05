from pathlib import Path

APP = Path("app.py")
BACKUP = Path("app.py.bak_before_bridge_showcase")

if not APP.exists():
    raise FileNotFoundError("app.py not found. Run this from your repo root.")

text = APP.read_text()

if not BACKUP.exists():
    BACKUP.write_text(text)

link = '("pages/9_Bridge_Infrastructure.py", "Bridge Infrastructure"),'

if link in text:
    print("Bridge Infrastructure link already exists.")
else:
    # Best effort: insert before Market Route Evidence or Evidence Downloads if found.
    targets = [
        '("pages/15_Market_Route_Evidence.py", "Market Route Evidence"),',
        '("pages/6_Evidence_Downloads.py", "Evidence Downloads"),',
        '("pages/8_Evidence_Hashes.py", "Evidence Hashes"),',
    ]

    inserted = False
    for target in targets:
        if target in text:
            text = text.replace(target, link + "\n        " + target)
            inserted = True
            break

    if not inserted:
        print("Could not auto-insert into page_links. Add this manually inside your page_links list:")
        print(link)
    else:
        APP.write_text(text)
        print("Updated app.py and created backup app.py.bak_before_bridge_showcase")

print("\nRun:")
print("python3 build_bridge_infrastructure_summary.py")
