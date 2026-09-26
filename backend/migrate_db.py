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
        cur.execute("PRAGMA table_info(tutor_interactions)")
        tutor_cols = [row[1] for row in cur.fetchall()]
        if tutor_cols:
            if "conversation_id" not in tutor_cols:
                cur.execute("ALTER TABLE tutor_interactions ADD COLUMN conversation_id VARCHAR(100)")
                print("  Added conversation_id to tutor_interactions")
            if "title" not in tutor_cols:
                cur.execute("ALTER TABLE tutor_interactions ADD COLUMN title VARCHAR(255)")
                print("  Added title to tutor_interactions")

        conn.commit()
        conn.close()

print("All SQLite databases migrated successfully.")
