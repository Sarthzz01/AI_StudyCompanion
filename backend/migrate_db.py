import sqlite3
import os

for path in ["ai_study_companion.db", "../ai_study_companion.db"]:
    if os.path.exists(path):
        abs_p = os.path.abspath(path)
        print(f"Migrating: {abs_p}")
        conn = sqlite3.connect(abs_p)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(materials)")
        cols = [row[1] for row in cur.fetchall()]
        if "raw_filename" not in cols:
            cur.execute("ALTER TABLE materials ADD COLUMN raw_filename VARCHAR(255)")
            print("  Added raw_filename")
        if "processing_status" not in cols:
            cur.execute("ALTER TABLE materials ADD COLUMN processing_status VARCHAR(50) DEFAULT 'ready'")
            print("  Added processing_status")
        conn.commit()
        conn.close()

print("All SQLite databases migrated successfully.")
