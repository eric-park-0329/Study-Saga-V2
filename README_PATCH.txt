
StudySaga — Patched Build
=========================
This package replaces broken files and adds:
• Gacha (bronze/silver/gold) with animated confetti, crystal costs, item pools, inventory updates
• Study screen with target minutes, live progress bar, completion rewards (+1 crystal per 5 minutes)
• Inventory screen listing acquired items
• Settings screen (nickname, gender, dark mode) with persistence
• Home screen showing crystals and quick nav
• Simple starfield background for subtle motion

How to run (desktop):
  python -m venv .venv
  # Windows: .venv\Scripts\activate
  # macOS/Linux: source .venv/bin/activate
  pip install -r requirements.txt
  python main.py

Files replaced/added:
  main.py
  auth.py
  db.py
  gacha.py
  color_utils.py
  *.kv (auth, home, study, gacha, inventory, settings)
  requirements.txt

Notes:
  - No external images required; UI uses Kivy canvas shapes.
  - On first run, a SQLite file 'studysaga.sqlite3' will be created and seeded with basic items.
  - You start with 100 crystals.
