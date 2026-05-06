from pathlib import Path
from datetime import datetime

APP = Path("app.py")
NEW = Path("app_one_page_polished.py")

if not NEW.exists():
    raise FileNotFoundError("app_one_page_polished.py is missing.")

if APP.exists():
    backup = Path(f"app_backup_before_one_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
    backup.write_text(APP.read_text())
    print(f"Backed up existing app.py to {backup}")

APP.write_text(NEW.read_text())
print("Installed polished one-page audit site as app.py")
