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

    print(f"Checking migration for: {abs_p}")
    conn = sqlite3.connect(abs_p)
    cur = conn.cursor()

    # 1. Check questions table
    cur.execute("PRAGMA table_info(questions)")
    q_info = cur.fetchall()
    q_cols = [row[1] for row in q_info]
    topic_id_row = next((r for r in q_info if r[1] == "topic_id"), None)
    if topic_id_row and topic_id_row[3] == 1:  # notnull == 1
        print("  Converting questions.topic_id to NULLABLE...")
        cur.execute("PRAGMA foreign_keys=off;")
        cur.execute("""
            CREATE TABLE questions_new (
                id INTEGER PRIMARY KEY,
                quiz_id INTEGER,
                topic_id INTEGER,
                material_id VARCHAR(100),
                topic_name VARCHAR(200),
                question_text TEXT NOT NULL,
                question_type VARCHAR(50) NOT NULL DEFAULT 'multiple_choice',
                options_json JSON NOT NULL DEFAULT '[]',
                correct_answer VARCHAR(255) NOT NULL,
                explanation TEXT,
                difficulty VARCHAR(50) NOT NULL DEFAULT 'medium',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            INSERT INTO questions_new (id, quiz_id, topic_id, material_id, topic_name, question_text, question_type, options_json, correct_answer, explanation, difficulty, created_at)
            SELECT id, quiz_id, topic_id, material_id, topic_name, question_text, question_type, options_json, correct_answer, explanation, difficulty, created_at FROM questions;
        """)
        cur.execute("DROP TABLE questions;")
        cur.execute("ALTER TABLE questions_new RENAME TO questions;")
        cur.execute("PRAGMA foreign_keys=on;")
        print("  questions.topic_id is now NULLABLE.")
    else:
        if "quiz_id" not in q_cols:
            cur.execute("ALTER TABLE questions ADD COLUMN quiz_id INTEGER")
            print("  Added questions.quiz_id")
        if "material_id" not in q_cols:
            cur.execute("ALTER TABLE questions ADD COLUMN material_id VARCHAR(100)")
            print("  Added questions.material_id")
        if "topic_name" not in q_cols:
            cur.execute("ALTER TABLE questions ADD COLUMN topic_name VARCHAR(200)")
            print("  Added questions.topic_name")

    # 2. Check flashcards table
    cur.execute("PRAGMA table_info(flashcards)")
    f_cols = [row[1] for row in cur.fetchall()]
    if "user_id" not in f_cols:
        cur.execute("ALTER TABLE flashcards ADD COLUMN user_id INTEGER")
        print("  Added flashcards.user_id")
    if "topic_name" not in f_cols:
        cur.execute("ALTER TABLE flashcards ADD COLUMN topic_name VARCHAR(200)")
        print("  Added flashcards.topic_name")
    if "source" not in f_cols:
        cur.execute("ALTER TABLE flashcards ADD COLUMN source VARCHAR(255)")
        print("  Added flashcards.source")

    # 3. Check quiz_attempts table
    cur.execute("PRAGMA table_info(quiz_attempts)")
    qa_info = cur.fetchall()
    qa_cols = [row[1] for row in qa_info]
    completed_at_row = next((r for r in qa_info if r[1] == "completed_at"), None)
    if completed_at_row and completed_at_row[3] == 1:
        print("  Converting quiz_attempts.completed_at to NULLABLE...")
        cur.execute("PRAGMA foreign_keys=off;")
        cur.execute("""
            CREATE TABLE quiz_attempts_new (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                quiz_id INTEGER,
                material_id VARCHAR(100),
                topic_id INTEGER,
                topic VARCHAR(200),
                difficulty VARCHAR(50) DEFAULT 'mixed',
                score INTEGER NOT NULL DEFAULT 0,
                total_questions INTEGER NOT NULL DEFAULT 0,
                accuracy FLOAT NOT NULL DEFAULT 0.0,
                status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
                answers_json JSON NOT NULL DEFAULT '[]',
                topic_results_json JSON NOT NULL DEFAULT '{}',
                difficulty_results_json JSON NOT NULL DEFAULT '{}',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            );
        """)
        cur.execute("""
            INSERT INTO quiz_attempts_new (id, user_id, quiz_id, material_id, topic_id, topic, difficulty, score, total_questions, accuracy, status, answers_json, topic_results_json, difficulty_results_json, created_at, completed_at)
            SELECT id, user_id, quiz_id, material_id, topic_id, topic, difficulty, score, total_questions, accuracy, status, answers_json, topic_results_json, difficulty_results_json, created_at, completed_at FROM quiz_attempts;
        """)
        cur.execute("DROP TABLE quiz_attempts;")
        cur.execute("ALTER TABLE quiz_attempts_new RENAME TO quiz_attempts;")
        cur.execute("PRAGMA foreign_keys=on;")
        print("  quiz_attempts.completed_at is now NULLABLE.")
    else:
        if "quiz_id" not in qa_cols:
            cur.execute("ALTER TABLE quiz_attempts ADD COLUMN quiz_id INTEGER")
            print("  Added quiz_attempts.quiz_id")
        if "topic" not in qa_cols:
            cur.execute("ALTER TABLE quiz_attempts ADD COLUMN topic VARCHAR(200)")
            print("  Added quiz_attempts.topic")
        if "difficulty" not in qa_cols:
            cur.execute("ALTER TABLE quiz_attempts ADD COLUMN difficulty VARCHAR(50) DEFAULT 'mixed'")
            print("  Added quiz_attempts.difficulty")
        if "status" not in qa_cols:
            cur.execute("ALTER TABLE quiz_attempts ADD COLUMN status VARCHAR(50) DEFAULT 'in_progress'")
            print("  Added quiz_attempts.status")
        if "topic_results_json" not in qa_cols:
            cur.execute("ALTER TABLE quiz_attempts ADD COLUMN topic_results_json JSON DEFAULT '{}'")
            print("  Added quiz_attempts.topic_results_json")
        if "difficulty_results_json" not in qa_cols:
            cur.execute("ALTER TABLE quiz_attempts ADD COLUMN difficulty_results_json JSON DEFAULT '{}'")
            print("  Added quiz_attempts.difficulty_results_json")
        if "created_at" not in qa_cols:
            cur.execute("ALTER TABLE quiz_attempts ADD COLUMN created_at DATETIME")
            print("  Added quiz_attempts.created_at")

    conn.commit()
    conn.close()

print("Phase 4 SQLite migration check complete.")
