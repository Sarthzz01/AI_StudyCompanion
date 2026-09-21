import sqlite3
import os

db_paths = [
    "ai_study_companion.db",
    "../ai_study_companion.db",
    os.path.join(os.path.dirname(__file__), "ai_study_companion.db"),
    os.path.join(os.path.dirname(__file__), "..", "ai_study_companion.db"),
]

seen = set()
for path in db_paths:
    abs_p = os.path.abspath(path)
    if abs_p in seen:
        continue
    seen.add(abs_p)

    if not os.path.exists(abs_p):
        continue

    print(f"Checking Phase 5 migration for: {abs_p}")
    conn = sqlite3.connect(abs_p)
    cur = conn.cursor()

    # 1. Check learner_models table
    cur.execute("PRAGMA table_info(learner_models)")
    lm_cols = [row[1] for row in cur.fetchall()]
    if "recent_performance_json" not in lm_cols:
        print("  Adding learner_models.recent_performance_json...")
        cur.execute("ALTER TABLE learner_models ADD COLUMN recent_performance_json JSON DEFAULT '[]'")

    # 2. Check study_sessions table
    cur.execute("PRAGMA table_info(study_sessions)")
    ss_cols = [row[1] for row in cur.fetchall()]
    if "topic" not in ss_cols:
        print("  Adding study_sessions.topic...")
        cur.execute("ALTER TABLE study_sessions ADD COLUMN topic VARCHAR(200)")

    # 3. Check goals table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
    if not cur.fetchone():
        print("  Creating goals table...")
        cur.execute("""
            CREATE TABLE goals (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL DEFAULT 'weekly',
                target INTEGER NOT NULL DEFAULT 5,
                current INTEGER NOT NULL DEFAULT 0,
                unit VARCHAR(50) NOT NULL DEFAULT 'topics',
                completed BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_goals_id ON goals(id);")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_goals_user_id ON goals(user_id);")

    conn.commit()
    conn.close()
    print(f"Phase 5 migration complete for: {abs_p}")
