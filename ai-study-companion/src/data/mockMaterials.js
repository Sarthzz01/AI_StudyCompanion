// Study material catalogue. Replace with GET /materials once FastAPI exists.
export const mockMaterials = [
  {
    id: 'data-structures',
    title: 'Data Structures',
    type: 'PDF',
    pages: 148,
    topicsCount: 8,
    lastStudied: '2 hours ago',
    progress: 72,
    color: 'brand',
    description:
      'Linear and non-linear structures, with an emphasis on trees, graphs and the complexity trade-offs behind each operation.',
    topics: [
      { name: 'Arrays & Linked Lists', progress: 100 },
      { name: 'Stacks & Queues', progress: 95 },
      { name: 'Binary Trees', progress: 80 },
      { name: 'BST Operations', progress: 48 },
      { name: 'Tree Traversal', progress: 92 },
      { name: 'Graph Traversal', progress: 35 },
      { name: 'Hashing', progress: 60 },
      { name: 'Sorting & Searching', progress: 70 },
    ],
    recentActivity: [
      { id: 1, label: 'Attempted a quiz on Tree Traversal', detail: 'Scored 8/10', time: '2 hours ago' },
      { id: 2, label: 'Generated a summary', detail: '4 sections, 12 key points', time: 'Yesterday' },
      { id: 3, label: 'Reviewed 15 flashcards', detail: '11 marked easy', time: '2 days ago' },
    ],
  },
  {
    id: 'dbms',
    title: 'Database Management Systems',
    type: 'PDF',
    pages: 210,
    topicsCount: 7,
    lastStudied: 'Yesterday',
    progress: 54,
    color: 'emerald',
    description:
      'Relational modelling, SQL, normalisation and the transaction guarantees that keep concurrent data consistent.',
    topics: [
      { name: 'ER Modelling', progress: 88 },
      { name: 'Relational Algebra', progress: 65 },
      { name: 'SQL Queries', progress: 76 },
      { name: 'Normalisation', progress: 42 },
      { name: 'Transactions & ACID', progress: 38 },
      { name: 'Indexing', progress: 30 },
      { name: 'Concurrency Control', progress: 25 },
    ],
    recentActivity: [
      { id: 1, label: 'Asked the AI tutor about normalisation', detail: '6 messages', time: 'Yesterday' },
      { id: 2, label: 'Bookmarked a summary section', detail: 'Transactions & ACID', time: '3 days ago' },
    ],
  },
  {
    id: 'operating-systems',
    title: 'Operating Systems',
    type: 'Notes',
    pages: 96,
    topicsCount: 6,
    lastStudied: '3 days ago',
    progress: 41,
    color: 'amber',
    description:
      'How the OS schedules work, shares memory safely and keeps processes from stepping on each other.',
    topics: [
      { name: 'Processes & Threads', progress: 70 },
      { name: 'CPU Scheduling', progress: 62 },
      { name: 'Synchronisation', progress: 34 },
      { name: 'Deadlocks', progress: 28 },
      { name: 'Memory Management', progress: 45 },
      { name: 'File Systems', progress: 20 },
    ],
    recentActivity: [
      { id: 1, label: 'Reviewed 10 flashcards', detail: '4 marked hard', time: '3 days ago' },
    ],
  },
  {
    id: 'computer-networks',
    title: 'Computer Networks',
    type: 'Slides',
    pages: 132,
    topicsCount: 6,
    lastStudied: 'Last week',
    progress: 23,
    color: 'sky',
    description:
      'Layered protocol design from physical signalling up to the application layer, with routing and congestion control in between.',
    topics: [
      { name: 'OSI & TCP/IP Models', progress: 55 },
      { name: 'Data Link Layer', progress: 30 },
      { name: 'Routing Algorithms', progress: 18 },
      { name: 'TCP & UDP', progress: 24 },
      { name: 'Congestion Control', progress: 10 },
      { name: 'Application Protocols', progress: 12 },
    ],
    recentActivity: [],
  },
]

export const getMaterialById = (id) => mockMaterials.find((m) => m.id === id)
