
# Optional one-off migration helper. You can run:
#   python migrate_once.py
# It will import db.py (which runs bootstrap + migrate) and exit.
import db as DB
DB.bootstrap()
print("Migration complete. DB at:", DB.DB_PATH)
