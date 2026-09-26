import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import Role, User, Profile
from app.models.subject import Subject, Topic
from app.models.material import Material
from app.models.learner import LearnerModel, Progress
from app.models.document import DocumentChunk, Summary
from app.models.study import Note
from app.services.auth_service import hash_password

logger = logging.getLogger("uvicorn.error")

def seed_database(db: Session):
    # Check if already seeded
    if db.query(Role).first():
        logger.info("Database already contains roles. Skipping initial seed.")
        return

    logger.info("Seeding database with initial roles, users, subjects, topics, and materials...")

    # 1. Roles
    student_role = Role(name="student", description="Student account with access to learning companion")
    instructor_role = Role(name="instructor", description="Instructor account with curriculum creation privileges")
    admin_role = Role(name="admin", description="Administrator with platform-wide management privileges")

    db.add_all([student_role, instructor_role, admin_role])
    db.commit()
    db.refresh(student_role)
    db.refresh(instructor_role)
    db.refresh(admin_role)

    # 2. Users & Profiles
    # Student
    student = User(
        email="student@study.edu",
        hashed_password=hash_password("password123"),
        role_id=student_role.id,
        is_active=True
    )
    # Instructor
    instructor = User(
        email="instructor@study.edu",
        hashed_password=hash_password("password123"),
        role_id=instructor_role.id,
        is_active=True
    )
    # Admin
    admin = User(
        email="admin@study.edu",
        hashed_password=hash_password("admin123"),
        role_id=admin_role.id,
        is_active=True
    )
    db.add_all([student, instructor, admin])
    db.commit()
    db.refresh(student)
    db.refresh(instructor)
    db.refresh(admin)

    # Student Profile
    student_profile = Profile(
        user_id=student.id,
        full_name="Alex Mercer",
        avatar_url=None,
        bio="Computer Science undergraduate passionate about algorithms and distributed systems.",
        preferences_json={
            "difficulty": "medium",
            "sessionLength": "30",
            "quizAlerts": True,
            "goalAlerts": True,
            "weeklySummary": False
        }
    )
    # Instructor Profile
    instructor_profile = Profile(
        user_id=instructor.id,
        full_name="Dr. Alan Turing",
        bio="Senior Professor of Computer Science.",
        preferences_json={"difficulty": "hard", "sessionLength": "60"}
    )
    # Admin Profile
    admin_profile = Profile(
        user_id=admin.id,
        full_name="System Admin",
        bio="Platform Administrator.",
        preferences_json={}
    )
    db.add_all([student_profile, instructor_profile, admin_profile])
    db.commit()

    # 3. Sample Subjects and Topics
    # Subject 1: Data Structures
    sub_ds = Subject(
        name="Data Structures & Algorithms",
        code="CS-201",
        description="Linear and non-linear data structures, trees, graphs, and algorithmic complexity.",
        created_by=instructor.id
    )
    # Subject 2: DBMS
    sub_db = Subject(
        name="Database Management Systems",
        code="CS-204",
        description="Relational modeling, SQL, normalization, and ACID transaction semantics.",
        created_by=instructor.id
    )
    # Subject 3: OS
    sub_os = Subject(
        name="Operating Systems",
        code="CS-205",
        description="Processes, threads, CPU scheduling, synchronization, deadlocks, and memory management.",
        created_by=instructor.id
    )
    # Subject 4: Networks
    sub_net = Subject(
        name="Computer Networks",
        code="CS-208",
        description="Layered architecture, TCP/IP protocol suite, routing algorithms, and congestion control.",
        created_by=instructor.id
    )
    db.add_all([sub_ds, sub_db, sub_os, sub_net])
    db.commit()
    db.refresh(sub_ds)
    db.refresh(sub_db)
    db.refresh(sub_os)
    db.refresh(sub_net)

    # Topics for DS
    topics_ds = [
        Topic(subject_id=sub_ds.id, name="Arrays & Linked Lists", order_index=1, difficulty_level="easy"),
        Topic(subject_id=sub_ds.id, name="Stacks & Queues", order_index=2, difficulty_level="easy"),
        Topic(subject_id=sub_ds.id, name="Binary Trees", order_index=3, difficulty_level="medium"),
        Topic(subject_id=sub_ds.id, name="BST Operations", order_index=4, difficulty_level="medium"),
        Topic(subject_id=sub_ds.id, name="Tree Traversal", order_index=5, difficulty_level="medium"),
        Topic(subject_id=sub_ds.id, name="Graph Traversal", order_index=6, difficulty_level="hard"),
        Topic(subject_id=sub_ds.id, name="Hashing", order_index=7, difficulty_level="medium"),
        Topic(subject_id=sub_ds.id, name="Sorting & Searching", order_index=8, difficulty_level="medium"),
    ]
    # Topics for DBMS
    topics_db = [
        Topic(subject_id=sub_db.id, name="ER Modelling", order_index=1, difficulty_level="easy"),
        Topic(subject_id=sub_db.id, name="Relational Algebra", order_index=2, difficulty_level="medium"),
        Topic(subject_id=sub_db.id, name="SQL Queries", order_index=3, difficulty_level="easy"),
        Topic(subject_id=sub_db.id, name="Normalisation", order_index=4, difficulty_level="hard"),
        Topic(subject_id=sub_db.id, name="Transactions & ACID", order_index=5, difficulty_level="medium"),
        Topic(subject_id=sub_db.id, name="Indexing", order_index=6, difficulty_level="hard"),
        Topic(subject_id=sub_db.id, name="Concurrency Control", order_index=7, difficulty_level="hard"),
    ]
    # Topics for OS
    topics_os = [
        Topic(subject_id=sub_os.id, name="Processes & Threads", order_index=1, difficulty_level="easy"),
        Topic(subject_id=sub_os.id, name="CPU Scheduling", order_index=2, difficulty_level="medium"),
        Topic(subject_id=sub_os.id, name="Synchronisation", order_index=3, difficulty_level="hard"),
        Topic(subject_id=sub_os.id, name="Deadlocks", order_index=4, difficulty_level="medium"),
        Topic(subject_id=sub_os.id, name="Memory Management", order_index=5, difficulty_level="hard"),
        Topic(subject_id=sub_os.id, name="File Systems", order_index=6, difficulty_level="medium"),
    ]
    # Topics for Networks
    topics_net = [
        Topic(subject_id=sub_net.id, name="OSI & TCP/IP Models", order_index=1, difficulty_level="easy"),
        Topic(subject_id=sub_net.id, name="Data Link Layer", order_index=2, difficulty_level="medium"),
        Topic(subject_id=sub_net.id, name="Routing Algorithms", order_index=3, difficulty_level="hard"),
        Topic(subject_id=sub_net.id, name="TCP & UDP", order_index=4, difficulty_level="medium"),
        Topic(subject_id=sub_net.id, name="Congestion Control", order_index=5, difficulty_level="hard"),
        Topic(subject_id=sub_net.id, name="Application Protocols", order_index=6, difficulty_level="easy"),
    ]

    all_topics = topics_ds + topics_db + topics_os + topics_net
    db.add_all(all_topics)
    db.commit()

    # 4. Materials matching mock catalogue
    m1 = Material(
        id="data-structures",
        user_id=student.id,
        subject_id=sub_ds.id,
        title="Data Structures",
        type="PDF",
        pages=148,
        topics_count=8,
        last_studied="2 hours ago",
        progress=72,
        color="brand",
        description="Linear and non-linear structures, with an emphasis on trees, graphs and the complexity trade-offs behind each operation.",
        topics_json=[
            {"name": "Arrays & Linked Lists", "progress": 100},
            {"name": "Stacks & Queues", "progress": 95},
            {"name": "Binary Trees", "progress": 80},
            {"name": "BST Operations", "progress": 48},
            {"name": "Tree Traversal", "progress": 92},
            {"name": "Graph Traversal", "progress": 35},
            {"name": "Hashing", "progress": 60},
            {"name": "Sorting & Searching", "progress": 70},
        ],
        recent_activity_json=[
            {"id": 1, "label": "Attempted a quiz on Tree Traversal", "detail": "Scored 8/10", "time": "2 hours ago"},
            {"id": 2, "label": "Generated a summary", "detail": "4 sections, 12 key points", "time": "Yesterday"},
            {"id": 3, "label": "Reviewed 15 flashcards", "detail": "11 marked easy", "time": "2 days ago"},
        ]
    )

    m2 = Material(
        id="dbms",
        user_id=student.id,
        subject_id=sub_db.id,
        title="Database Management Systems",
        type="PDF",
        pages=210,
        topics_count=7,
        last_studied="Yesterday",
        progress=54,
        color="emerald",
        description="Relational modelling, SQL, normalisation and the transaction guarantees that keep concurrent data consistent.",
        topics_json=[
            {"name": "ER Modelling", "progress": 88},
            {"name": "Relational Algebra", "progress": 65},
            {"name": "SQL Queries", "progress": 76},
            {"name": "Normalisation", "progress": 42},
            {"name": "Transactions & ACID", "progress": 38},
            {"name": "Indexing", "progress": 30},
            {"name": "Concurrency Control", "progress": 25},
        ],
        recent_activity_json=[
            {"id": 1, "label": "Asked the AI tutor about normalisation", "detail": "6 messages", "time": "Yesterday"},
            {"id": 2, "label": "Bookmarked a summary section", "detail": "Transactions & ACID", "time": "3 days ago"},
        ]
    )

    m3 = Material(
        id="operating-systems",
        user_id=student.id,
        subject_id=sub_os.id,
        title="Operating Systems",
        type="Notes",
        pages=96,
        topics_count=6,
        last_studied="3 days ago",
        progress=41,
        color="amber",
        description="How the OS schedules work, shares memory safely and keeps processes from stepping on each other.",
        topics_json=[
            {"name": "Processes & Threads", "progress": 70},
            {"name": "CPU Scheduling", "progress": 62},
            {"name": "Synchronisation", "progress": 34},
            {"name": "Deadlocks", "progress": 28},
            {"name": "Memory Management", "progress": 45},
            {"name": "File Systems", "progress": 20},
        ],
        recent_activity_json=[
            {"id": 1, "label": "Reviewed 10 flashcards", "detail": "4 marked hard", "time": "3 days ago"},
        ]
    )

    m4 = Material(
        id="computer-networks",
        user_id=student.id,
        subject_id=sub_net.id,
        title="Computer Networks",
        type="Slides",
        pages=132,
        topics_count=6,
        last_studied="Last week",
        progress=23,
        color="sky",
        description="Layered protocol design from physical signalling up to the application layer, with routing and congestion control in between.",
        topics_json=[
            {"name": "OSI & TCP/IP Models", "progress": 55},
            {"name": "Data Link Layer", "progress": 30},
            {"name": "Routing Algorithms", "progress": 18},
            {"name": "TCP & UDP", "progress": 24},
            {"name": "Congestion Control", "progress": 10},
            {"name": "Application Protocols", "progress": 12},
        ],
        recent_activity_json=[]
    )

    db.add_all([m1, m2, m3, m4])
    db.commit()

    # 5. Learner Model seed for Alex Mercer
    lm1 = LearnerModel(
        user_id=student.id,
        topic_id=topics_ds[4].id,  # Tree Traversal
        topic="Tree Traversal",
        mastery=85.0,
        recall_reliability=0.88,
        quiz_accuracy=80.0,
        flashcard_performance=90.0,
        viva_performance=82.0,
        difficulty="medium",
        last_reviewed=datetime.utcnow()
    )
    lm2 = LearnerModel(
        user_id=student.id,
        topic_id=topics_db[3].id,  # Normalisation
        topic="Normalisation",
        mastery=42.0,
        recall_reliability=0.45,
        quiz_accuracy=40.0,
        flashcard_performance=48.0,
        viva_performance=38.0,
        difficulty="hard",
        last_reviewed=datetime.utcnow()
    )
    db.add_all([lm1, lm2])

    # 6. Progress seed
    prog = Progress(
        user_id=student.id,
        overall_accuracy=74.5,
        total_study_time_minutes=320,
        questions_attempted=142,
        quizzes_completed=18,
        current_streak_days=5
    )
    db.add(prog)
    db.commit()

    logger.info("Database seeding completed successfully!")

def seed_phase3_chunks(db: Session):
    """Seed initial chunks and summaries for pre-seeded materials if not present."""
    from app.services.rag_service import rag_service

    if db.query(DocumentChunk).first():
        return

    logger.info("Seeding Phase 3 document chunks and embeddings for Data Structures and DBMS...")

    ds_chunks_data = [
        {
            "material_id": "data-structures",
            "chunk_index": 0,
            "page_number": 12,
            "content": (
                "Binary Trees and Binary Search Tree (BST) Fundamentals: A binary tree is a hierarchical data structure in which each node "
                "has at most two children, termed the left child and right child. The Binary Search Tree invariant requires that for every node X, "
                "all keys in the left subtree of X are strictly less than key(X), and all keys in the right subtree are strictly greater than key(X). "
                "Because comparisons halve the search space at each node, search, insertion, and minimum/maximum retrieval run in O(h) time, "
                "where h is the tree height. In a balanced BST (such as an AVL or Red-Black tree), h = O(log n), providing logarithmic performance. "
                "However, if keys are inserted in strictly sorted order without balancing, the tree degenerates into a linear linked list of height n, "
                "yielding worst-case O(n) performance."
            )
        },
        {
            "material_id": "data-structures",
            "chunk_index": 1,
            "page_number": 15,
            "content": (
                "Binary Search Tree Deletion Algorithms: Deleting a key from a binary search tree entails three distinct topological cases: "
                "Case 1 (Leaf Node): If the target node has no children, simply sever the pointer from its parent. "
                "Case 2 (Single Child): If the target node has exactly one child, bypass the node by setting its parent's child pointer to point directly "
                "to the node's single child. "
                "Case 3 (Two Children): If the target node has two children, locate its in-order successor (the minimum node in its right subtree) "
                "or its in-order predecessor (maximum in left subtree). Copy the successor's key into the target node, and then recursively delete "
                "the successor node from the right subtree. Because finding the successor takes at most O(h) time, overall deletion complexity is O(h)."
            )
        },
        {
            "material_id": "data-structures",
            "chunk_index": 2,
            "page_number": 18,
            "content": (
                "Binary Tree Traversals and Reconstruction: Systematic traversal of binary tree nodes falls into Depth-First and Breadth-First strategies. "
                "1. Pre-order traversal (Root -> Left -> Right) processes the current node before subtrees, ideal for serializing or duplicating tree topology. "
                "2. In-order traversal (Left -> Root -> Right) visits nodes in ascending order on any valid binary search tree. "
                "3. Post-order traversal (Left -> Right -> Root) inspects children prior to the root, providing the memory-safe sequence for deallocating nodes. "
                "4. Level-order traversal walks the tree horizontally from root to leaves using a First-In-First-Out (FIFO) queue. "
                "To uniquely reconstruct an arbitrary binary tree, an In-order traversal sequence combined with either a Pre-order or Post-order sequence is strictly required."
            )
        },
        {
            "material_id": "data-structures",
            "chunk_index": 3,
            "page_number": 64,
            "content": (
                "Graph Representations and Breadth-First Search (BFS): Graphs G = (V, E) can be represented with an Adjacency Matrix (space O(V^2)) "
                "or an Adjacency List (space O(V + E)). Breadth-First Search explores graph vertices in concentric layers outward from a designated start vertex. "
                "BFS utilizes a FIFO queue. Every adjacent undiscovered neighbor is marked as visited and enqueued. Because BFS discovers all vertices at distance d "
                "before inspecting vertices at distance d + 1, BFS is guaranteed to discover the shortest path in unweighted graphs. "
                "Its running time complexity on an adjacency list is O(V + E)."
            )
        },
        {
            "material_id": "data-structures",
            "chunk_index": 4,
            "page_number": 67,
            "content": (
                "Depth-First Search (DFS) and Graph Algorithms: DFS progresses along a path as deeply as possible before backtracking to unvisited branches. "
                "DFS is implemented via recursion or an explicit LIFO stack. The algorithm records discovery and finishing timestamps for each vertex. "
                "Key applications include: cycle detection in directed graphs (indicated by the presence of a back-edge), topological sorting for Directed "
                "Acyclic Graphs (ordering vertices by decreasing finish time), and finding strongly connected components (Kosaraju's and Tarjan's algorithms). "
                "DFS runs in O(V + E) time on an adjacency list and requires a visited set to avoid infinite cycles."
            )
        },
        {
            "material_id": "data-structures",
            "chunk_index": 5,
            "page_number": 95,
            "content": (
                "Hashing and Collision Resolution: Hash tables achieve efficient average-case dictionary operations (lookup, insert, delete in O(1) time). "
                "A hash function maps an arbitrary key universe into a finite bucket range [0, m - 1]. Collisions occur when two distinct keys map to the same bucket. "
                "Two principal resolution strategies exist: "
                "1. Separate Chaining: Each bucket stores a pointer to a linked list of entries. Average lookup time is O(1 + alpha), where alpha = n / m is the load factor. "
                "2. Open Addressing: All elements reside directly within the table array. On collision, probe sequences (Linear Probing, Quadratic Probing, or Double Hashing) "
                "are examined until an empty slot is located."
            )
        }
    ]

    dbms_chunks_data = [
        {
            "material_id": "dbms",
            "chunk_index": 0,
            "page_number": 45,
            "content": (
                "Relational Data Model and Integrity Constraints: The relational model structures database storage into mathematical relations (tables) "
                "of tuples (rows) and attributes (columns). Integrity constraints safeguard data consistency: "
                "1. Entity Integrity: Every relation must possess a primary key, and no primary key attribute may ever contain a NULL value. "
                "2. Referential Integrity: A foreign key in a referencing relation must either match a valid candidate key value in the referenced relation, "
                "or be entirely NULL. Violations on deletion or update are managed via RESTRICT, CASCADE, or SET NULL policies. "
                "3. Domain Constraints: Attribute values must belong to the prescribed atomic data type domain."
            )
        },
        {
            "material_id": "dbms",
            "chunk_index": 1,
            "page_number": 74,
            "content": (
                "Database Normalization and Normal Forms: Normalization eliminates data redundancy and prevents update, insertion, and deletion anomalies "
                "by decomposing relations based on functional dependencies (FDs). "
                "1. First Normal Form (1NF): All attribute values must be atomic and relations cannot contain repeating groups. "
                "2. Second Normal Form (2NF): Relation is in 1NF and contains no partial dependencies (every non-prime attribute is fully functionally dependent "
                "on every candidate key). "
                "3. Third Normal Form (3NF): Relation is in 2NF and contains no transitive dependencies (for every non-trivial FD X -> Y, either X is a superkey "
                "or Y is a prime attribute). "
                "4. Boyce-Codd Normal Form (BCNF): For every non-trivial FD X -> Y, X must be a superkey."
            )
        },
        {
            "material_id": "dbms",
            "chunk_index": 2,
            "page_number": 131,
            "content": (
                "Transaction Processing and ACID Guarantees: A transaction is a logical unit of database processing that must guarantee ACID properties: "
                "1. Atomicity: All operations in a transaction succeed or all are rolled back. Enforced via Write-Ahead Logging (WAL) and undo logging. "
                "2. Consistency: A transaction transitions the database from one consistent state satisfying all invariants to another consistent state. "
                "3. Isolation: Intermediate transaction states remain invisible to other concurrent transactions. Enforced via Concurrency Control mechanisms "
                "such as Two-Phase Locking (2PL) and Strict 2PL. "
                "4. Durability: Once a transaction commits, its effects persist across system crashes. Enforced via non-volatile storage flushing."
            )
        }
    ]

    all_seed_chunks = ds_chunks_data + dbms_chunks_data
    texts = [c["content"] for c in all_seed_chunks]
    embeddings = rag_service.generate_embeddings(texts)

    for idx, c in enumerate(all_seed_chunks):
        emb = embeddings[idx] if idx < len(embeddings) else None
        chunk_obj = DocumentChunk(
            material_id=c["material_id"],
            chunk_index=c["chunk_index"],
            page_number=c["page_number"],
            content=c["content"],
            token_count=len(c["content"].split()),
            embedding_json=emb
        )
        db.add(chunk_obj)

    db.commit()
    logger.info(f"Phase 3 document chunks seeded: {len(all_seed_chunks)} chunks added.")

def seed_phase9_instructor_data(db: Session):
    """
    Seeds additional realistic student cohorts (Beatrice, Carlos, Divya)
    along with sample Assessments, Submissions, and Feedback so the Instructor Module
    displays rich, immediate class analytics.
    """
    from app.models.assessment import Assessment, AssessmentAssignment, AssessmentSubmission, InstructorFeedback
    from datetime import timedelta

    # Check if student role exists
    student_role = db.query(Role).filter(Role.name == "student").first()
    instructor_user = db.query(User).filter(User.email == "instructor@study.edu").first()
    if not student_role or not instructor_user:
        return

    # 1. Additional Students
    extra_students_data = [
        {
            "email": "beatrice@study.edu",
            "name": "Beatrice Vance",
            "bio": "Distinguished scholar focusing on Distributed Consensus & Database Systems.",
            "study_mins": 480,
            "streak": 12,
            "topics": [
                {"topic": "Deadlocks", "mastery": 92.0, "quiz": 95.0, "flashcard": 90.0, "viva": 90.0, "recall": 0.95},
                {"topic": "Routing Algorithms", "mastery": 88.0, "quiz": 90.0, "flashcard": 85.0, "viva": 88.0, "recall": 0.90},
                {"topic": "Transactions & ACID", "mastery": 85.0, "quiz": 88.0, "flashcard": 82.0, "viva": 84.0, "recall": 0.88},
                {"topic": "Tree Traversal", "mastery": 90.0, "quiz": 92.0, "flashcard": 88.0, "viva": 89.0, "recall": 0.92},
            ]
        },
        {
            "email": "carlos@study.edu",
            "name": "Carlos Mendez",
            "bio": "Undergraduate student keen on System Architecture and Network Engineering.",
            "study_mins": 310,
            "streak": 5,
            "topics": [
                {"topic": "Deadlocks", "mastery": 74.0, "quiz": 75.0, "flashcard": 70.0, "viva": 72.0, "recall": 0.78},
                {"topic": "Routing Algorithms", "mastery": 68.0, "quiz": 70.0, "flashcard": 65.0, "viva": 66.0, "recall": 0.72},
                {"topic": "Transactions & ACID", "mastery": 76.0, "quiz": 78.0, "flashcard": 74.0, "viva": 75.0, "recall": 0.80},
                {"topic": "Tree Traversal", "mastery": 70.0, "quiz": 72.0, "flashcard": 68.0, "viva": 68.0, "recall": 0.75},
            ]
        },
        {
            "email": "divya@study.edu",
            "name": "Divya Sharma",
            "bio": "Second-year CS student focusing on foundational Operating Systems and algorithms.",
            "study_mins": 140,
            "streak": 2,
            "topics": [
                {"topic": "Deadlocks", "mastery": 45.0, "quiz": 45.0, "flashcard": 40.0, "viva": 48.0, "recall": 0.48},
                {"topic": "Routing Algorithms", "mastery": 52.0, "quiz": 50.0, "flashcard": 55.0, "viva": 50.0, "recall": 0.55},
                {"topic": "Transactions & ACID", "mastery": 42.0, "quiz": 40.0, "flashcard": 45.0, "viva": 40.0, "recall": 0.44},
                {"topic": "Tree Traversal", "mastery": 55.0, "quiz": 58.0, "flashcard": 52.0, "viva": 54.0, "recall": 0.58},
            ]
        }
    ]

    for item in extra_students_data:
        existing = db.query(User).filter(User.email == item["email"]).first()
        if not existing:
            u = User(
                email=item["email"],
                hashed_password=hash_password("password123"),
                role_id=student_role.id,
                is_active=True
            )
            db.add(u)
            db.commit()
            db.refresh(u)

            prof = Profile(
                user_id=u.id,
                full_name=item["name"],
                bio=item["bio"],
                preferences_json={"difficulty": "medium", "sessionLength": "30"}
            )
            prog = Progress(
                user_id=u.id,
                total_study_time_minutes=item["study_mins"],
                current_streak_days=item["streak"],
                last_active=datetime.utcnow()
            )
            db.add_all([prof, prog])
            db.commit()

            # Add LearnerModel records
            for t in item["topics"]:
                lm = LearnerModel(
                    user_id=u.id,
                    topic=t["topic"],
                    mastery=t["mastery"],
                    quiz_accuracy=t["quiz"],
                    flashcard_performance=t["flashcard"],
                    viva_performance=t["viva"],
                    recall_reliability=t["recall"],
                    last_reviewed=datetime.utcnow() - timedelta(days=1),
                    next_review=datetime.utcnow() + timedelta(days=3)
                )
                db.add(lm)
            db.commit()

    # 2. Sample Assessment
    sample_assessment = db.query(Assessment).filter(Assessment.instructor_id == instructor_user.id).first()
    if not sample_assessment:
        sample_assessment = Assessment(
            instructor_id=instructor_user.id,
            title="Midterm Assessment: Concurrency & Deadlock Mechanics",
            description="Comprehensive evaluation of deadlock conditions, Banker's Algorithm, and prevention strategies.",
            topic="Deadlocks",
            difficulty="medium",
            time_limit_minutes=25,
            total_points=100,
            pass_percentage=60.0,
            questions_json=[
                {
                    "id": 1,
                    "question_text": "Which condition is NOT one of the four Coffman conditions necessary for deadlock to occur?",
                    "question_type": "multiple_choice",
                    "options": [
                        "Mutual Exclusion",
                        "Preemption Allowed",
                        "Hold and Wait",
                        "Circular Wait"
                    ],
                    "correct_answer": 1,
                    "points": 25,
                    "explanation": "No preemption is the required condition; allowing preemption eliminates deadlock.",
                    "concept_tested": "Coffman Conditions",
                    "difficulty": "easy"
                },
                {
                    "id": 2,
                    "question_text": "What is the primary operational mechanism of the Banker's Algorithm?",
                    "question_type": "multiple_choice",
                    "options": [
                        "To dynamically verify that granting a resource request leaves the system in a safe state.",
                        "To terminate threads immediately when circular wait is detected.",
                        "To enforce strict global total ordering on all resource acquisition requests.",
                        "To serialize all concurrent requests through a single atomic lock."
                    ],
                    "correct_answer": 0,
                    "points": 25,
                    "explanation": "The Banker's Algorithm checks if a safe allocation sequence exists before allocating.",
                    "concept_tested": "Deadlock Avoidance",
                    "difficulty": "medium"
                },
                {
                    "id": 3,
                    "question_text": "How does imposing a total ordering on resource allocation prevent deadlocks?",
                    "question_type": "multiple_choice",
                    "options": [
                        "It eliminates the Circular Wait condition by ensuring cycles cannot form in the resource graph.",
                        "It makes resources non-exclusive so multiple processes can access them simultaneously.",
                        "It allows the operating system to preempt held locks without transaction rollback.",
                        "It automatically doubles available system resources when contention arises."
                    ],
                    "correct_answer": 0,
                    "points": 25,
                    "explanation": "Imposing an order on resource acquisition prevents circular wait chains from forming.",
                    "concept_tested": "Deadlock Prevention",
                    "difficulty": "medium"
                },
                {
                    "id": 4,
                    "question_text": "In Resource Allocation Graph (RAG) analysis with multiple instances per resource type, a cycle indicates:",
                    "question_type": "multiple_choice",
                    "options": [
                        "A potential deadlock, but not a guaranteed deadlock unless all instances are tied up.",
                        "A guaranteed immediate deadlock under all conditions.",
                        "A guaranteed safe state with optimal throughput.",
                        "A memory leak in the kernel scheduler."
                    ],
                    "correct_answer": 0,
                    "points": 25,
                    "explanation": "With multiple instances, a cycle is a necessary but not sufficient condition for deadlock.",
                    "concept_tested": "RAG Graph Theory",
                    "difficulty": "hard"
                }
            ],
            is_published=True
        )
        db.add(sample_assessment)
        db.commit()
        db.refresh(sample_assessment)

        # Create Assignment
        assignment = AssessmentAssignment(
            assessment_id=sample_assessment.id,
            instructor_id=instructor_user.id,
            assigned_to_all=True,
            due_date=datetime.utcnow() + timedelta(days=7),
            instructions="Complete this assessment in one sitting. Review Deadlock Coffman conditions beforehand.",
            status="active"
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Seed Sample Submissions
        all_students = db.query(User).filter(User.role_id == student_role.id).all()
        score_mappings = {
            "student@study.edu": (75.0, True),
            "beatrice@study.edu": (100.0, True),
            "carlos@study.edu": (75.0, True),
            "divya@study.edu": (50.0, False),
        }
        for st in all_students:
            score_info = score_mappings.get(st.email, (70.0, True))
            sub = AssessmentSubmission(
                assessment_id=sample_assessment.id,
                assignment_id=assignment.id,
                student_id=st.id,
                score=score_info[0],
                total_points=100,
                percentage=score_info[0],
                passed=score_info[1],
                time_spent_seconds=920,
                answers_json=[],
                status="graded",
                submitted_at=datetime.utcnow() - timedelta(hours=12)
            )
            db.add(sub)

        # Seed Sample Feedback
        divya = db.query(User).filter(User.email == "divya@study.edu").first()
        if divya:
            fb = InstructorFeedback(
                instructor_id=instructor_user.id,
                student_id=divya.id,
                assessment_id=sample_assessment.id,
                topic="Deadlocks",
                feedback_type="topic_intervention",
                feedback_text="Divya, your score on Deadlocks indicates a need to review the four Coffman conditions and the difference between prevention and avoidance algorithms. I recommend doing active recall flashcards.",
                action_items_json=[
                    "Review Coffman conditions lecture notes",
                    "Complete 10 Deadlock flashcards in AI Companion",
                    "Retake a 5-question Deadlock quiz"
                ],
                is_read=False
            )
            db.add(fb)

        db.commit()
        logger.info("Phase 9 Instructor seed data successfully created.")

def seed_notes_data(db: Session):
    """Seed initial high-yield study notes for students."""
    student_user = db.query(User).filter(User.email == "student@study.edu").first()
    if not student_user:
        return

    if db.query(Note).filter(Note.user_id == student_user.id).first():
        return

    note1 = Note(
        user_id=student_user.id,
        title="Binary Search Trees: Search, Insertion, and Balancing",
        topic="Data Structures",
        content="""## 1. Core Principles of Binary Search Trees (BST)
A Binary Search Tree is an ordered node-based tree data structure where each node satisfies the BST invariant:
- The left subtree of a node contains only keys less than the node's key.
- The right subtree of a node contains only keys greater than the node's key.
- Both left and right subtrees must also be binary search trees.

## 2. Inorder Traversal Property
An inorder traversal (Left -> Node -> Right) of any valid Binary Search Tree processes and visits elements in strictly sorted ascending order. This makes BSTs optimal for range queries and dynamic sorted sets.

## 3. Algorithmic Complexity
- Average Time Complexity: O(log N) for Search, Insert, and Delete in balanced trees.
- Worst Time Complexity: O(N) when inserted in strictly sorted order, causing degeneration into a singly-linked list.
- Balanced Alternatives: AVL Trees and Red-Black Trees guarantee O(log N) height via self-balancing rotations.""",
        key_points_json=[
            "BST Invariant: Left child < Node < Right child for all subtrees.",
            "Inorder traversal always yields sorted keys in ascending sequence.",
            "Degenerate BST behaves as a linked list with O(N) search time.",
            "Self-balancing variants (AVL, Red-Black) maintain O(log N) height through tree rotations."
        ],
        examples_json=[
            "def search_bst(root, key):\n    if root is None or root.val == key:\n        return root\n    if key < root.val:\n        return search_bst(root.left, key)\n    return search_bst(root.right, key)"
        ],
        tags_json=["trees", "algorithms", "data-structures", "search"],
        is_favorite=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    note2 = Note(
        user_id=student_user.id,
        title="Operating Systems: Coffman Conditions & Deadlock Avoidance",
        topic="Operating Systems",
        content="""## 1. The Four Coffman Conditions
Deadlock can occur if and only if all four of the following conditions hold simultaneously in a system:
1. Mutual Exclusion: At least one resource must be held in a non-shareable mode.
2. Hold and Wait: A process must be holding at least one resource and requesting additional resources held by other processes.
3. No Preemption: Resources cannot be forcibly seized from a process; they can only be released voluntarily.
4. Circular Wait: A closed chain of processes exists such that each process holds resources needed by the next process in the chain.

## 2. Deadlock Handling Strategies
- Prevention: Invalidate at least one of the four Coffman conditions (e.g., enforce strict resource ordering to break circular wait).
- Avoidance: Banker's Algorithm dynamically inspects state to ensure the system never enters an unsafe state.
- Detection & Recovery: Allow deadlocks to occur, periodically run cycle-detection on Resource Allocation Graphs (RAG), and preempt or terminate processes to break cycles.""",
        key_points_json=[
            "All four Coffman conditions must hold concurrently for a deadlock to exist.",
            "Breaking any single Coffman condition renders deadlock impossible.",
            "Banker's Algorithm ensures safe states using resource allocation and claim matrices.",
            "Resource Allocation Graph (RAG) cycles indicate deadlock when resources have single units."
        ],
        examples_json=[
            "// Breaking Circular Wait via Global Resource Ordering:\nvoid acquire_locks(int r1, int r2) {\n    if (r1 < r2) {\n        lock(r1); lock(r2);\n    } else {\n        lock(r2); lock(r1);\n    }\n}"
        ],
        tags_json=["operating-systems", "concurrency", "deadlocks", "process-synchronization"],
        is_favorite=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add_all([note1, note2])
    db.commit()
    logger.info("Successfully seeded initial study notes.")
