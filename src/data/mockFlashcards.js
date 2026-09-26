// Flashcards grouped by material id.
export const mockFlashcards = {
  'data-structures': [
    {
      id: 'ds-1',
      topic: 'BST Operations',
      front: 'What is a Binary Search Tree?',
      back: 'A binary tree where every node in the left subtree holds a smaller key than the node, and every node in the right subtree holds a larger key. This ordering makes search, insert and delete O(log n) on a balanced tree.',
      source: 'Data Structures.pdf — Page 12',
    },
    {
      id: 'ds-2',
      topic: 'Tree Traversal',
      front: 'In which order does in-order traversal visit nodes?',
      back: 'Left subtree, then the node itself, then the right subtree. On a BST this returns the keys in ascending sorted order.',
      source: 'Data Structures.pdf — Page 18',
    },
    {
      id: 'ds-3',
      topic: 'Graph Traversal',
      front: 'When would you pick BFS over DFS?',
      back: 'When you need the shortest path in an unweighted graph, or when the answer is likely close to the source. BFS explores level by level using a queue; DFS goes deep using a stack or recursion.',
      source: 'Data Structures.pdf — Page 64',
    },
    {
      id: 'ds-4',
      topic: 'Sorting & Searching',
      front: 'Why is merge sort O(n log n) in every case?',
      back: 'The array is always halved log n times, and each level of merging touches all n elements once. The split does not depend on the data, so best, average and worst cases match.',
      source: 'Data Structures.pdf — Page 88',
    },
    {
      id: 'ds-5',
      topic: 'Hashing',
      front: 'What is a collision, and how does chaining resolve it?',
      back: 'A collision happens when two keys hash to the same bucket. Chaining stores a linked list per bucket, so colliding keys sit in the same list and lookup scans that short list.',
      source: 'Data Structures.pdf — Page 102',
    },
  ],
  dbms: [
    {
      id: 'db-1',
      topic: 'Normalisation',
      front: 'What problem does 3NF remove that 2NF does not?',
      back: 'Transitive dependencies — a non-key attribute depending on another non-key attribute. Removing them stops update anomalies where the same fact is stored in several rows.',
      source: 'DBMS.pdf — Page 74',
    },
    {
      id: 'db-2',
      topic: 'Transactions & ACID',
      front: 'What does isolation guarantee?',
      back: 'Concurrent transactions produce the same result as if they had run one after another. Weaker isolation levels trade this guarantee for throughput.',
      source: 'DBMS.pdf — Page 131',
    },
    {
      id: 'db-3',
      topic: 'SQL Queries',
      front: 'How does HAVING differ from WHERE?',
      back: 'WHERE filters rows before grouping; HAVING filters groups after aggregation. Aggregate functions can only appear in HAVING.',
      source: 'DBMS.pdf — Page 58',
    },
  ],
  'operating-systems': [
    {
      id: 'os-1',
      topic: 'Deadlocks',
      front: 'Name the four conditions required for a deadlock.',
      back: 'Mutual exclusion, hold and wait, no preemption, and circular wait. Breaking any one of them prevents deadlock.',
      source: 'Operating Systems notes — Page 41',
    },
    {
      id: 'os-2',
      topic: 'CPU Scheduling',
      front: 'Why can Shortest Job First starve processes?',
      back: 'A steady stream of short jobs keeps jumping ahead of a long job, so the long job may never reach the CPU. Ageing raises a waiting job’s priority over time to fix this.',
      source: 'Operating Systems notes — Page 22',
    },
    {
      id: 'os-3',
      topic: 'Memory Management',
      front: 'What is thrashing?',
      back: 'A process spends more time swapping pages in and out than executing, because its working set does not fit in the frames it has been given.',
      source: 'Operating Systems notes — Page 63',
    },
  ],
  'computer-networks': [
    {
      id: 'cn-1',
      topic: 'TCP & UDP',
      front: 'When is UDP the better choice?',
      back: 'When low latency matters more than reliability — live video, voice, gaming, DNS. UDP skips handshakes, ordering and retransmission.',
      source: 'Computer Networks slides — Slide 47',
    },
    {
      id: 'cn-2',
      topic: 'Routing Algorithms',
      front: 'How does distance vector routing differ from link state?',
      back: 'Distance vector shares its whole routing table with neighbours only. Link state floods local link costs to everyone, so each router builds a full map and runs Dijkstra on it.',
      source: 'Computer Networks slides — Slide 62',
    },
  ],
}

export const getFlashcardsFor = (materialId) => mockFlashcards[materialId] || []
