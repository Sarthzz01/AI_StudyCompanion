import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import Role, User, Profile
from app.models.subject import Subject, Topic
from app.models.material import Material
from app.models.learner import LearnerModel, Progress
from app.models.document import DocumentChunk, Summary
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
