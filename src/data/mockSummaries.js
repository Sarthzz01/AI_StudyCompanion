// AI-generated summaries, one entry per material id.
export const mockSummaries = {
  'data-structures': {
    generatedAt: '2 hours ago',
    keyConcepts: ['Binary Search Tree', 'Traversal order', 'Balancing', 'Amortised cost', 'Adjacency list'],
    sections: [
      {
        id: 's1',
        title: 'Binary Trees',
        body: 'A binary tree gives each node at most two children. Height decides the cost of nearly every operation, so a tree that grows to the left or right like a list loses the advantage over an array. Complete and full trees are the shapes worth recognising in exam questions.',
        points: [
          'Height h holds at most 2^(h+1) − 1 nodes.',
          'A skewed tree degrades to O(n) behaviour.',
          'Array representation works well for complete trees.',
        ],
      },
      {
        id: 's2',
        title: 'Binary Search Trees',
        body: 'The BST property — smaller keys left, larger keys right — turns search into repeated halving. Insertion attaches a leaf; deletion is the only operation with real case analysis, because a node with two children must be replaced by its in-order successor.',
        points: [
          'Search, insert and delete are O(h).',
          'Deletion has three cases: leaf, one child, two children.',
          'Self-balancing variants (AVL, red-black) keep h at O(log n).',
        ],
      },
      {
        id: 's3',
        title: 'Tree Traversal',
        body: 'Pre-order, in-order and post-order differ only in when the node is visited relative to its subtrees. In-order on a BST returns sorted keys; post-order is the safe order for freeing memory; level-order needs a queue rather than recursion.',
        points: [
          'In-order on a BST outputs ascending keys.',
          'Post-order visits children before the parent.',
          'Level-order uses a queue, mirroring BFS.',
        ],
      },
      {
        id: 's4',
        title: 'Complexity',
        body: 'Compare structures by the operation you perform most. Hash tables win on average lookup but lose ordering; balanced trees keep order at a log n cost; arrays win on cache locality and random access but pay for insertion.',
        points: [
          'Balanced tree operations: O(log n).',
          'Hash table average lookup: O(1), worst case O(n).',
          'DFS and BFS on an adjacency list: O(V + E).',
        ],
      },
    ],
  },
  dbms: {
    generatedAt: 'Yesterday',
    keyConcepts: ['Functional dependency', 'ACID', 'Serialisability', 'Clustered index', 'Join'],
    sections: [
      {
        id: 's1',
        title: 'Relational Model & SQL',
        body: 'Tables, keys and constraints are the whole model. Most SQL marks are lost on grouping: WHERE filters rows before aggregation, HAVING filters groups afterwards, and an aggregate cannot appear in WHERE.',
        points: ['Primary key implies unique and not null.', 'WHERE runs before GROUP BY, HAVING after.', 'Joins default to inner unless stated.'],
      },
      {
        id: 's2',
        title: 'Normalisation',
        body: 'Each normal form removes one class of redundancy: 1NF atomic values, 2NF partial dependencies, 3NF transitive dependencies, BCNF determinants that are not candidate keys. Work from the functional dependency set, not intuition.',
        points: ['2NF only matters with composite keys.', '3NF removes transitive dependencies.', 'BCNF may cost dependency preservation.'],
      },
      {
        id: 's3',
        title: 'Transactions & ACID',
        body: 'Atomicity and durability are recovery properties handled by logging; consistency and isolation are concurrency properties handled by locking or timestamps. Isolation levels trade correctness for throughput.',
        points: ['Write-ahead logging supports rollback and recovery.', 'Lower isolation allows dirty or phantom reads.', 'Two-phase locking gives conflict serialisability.'],
      },
      {
        id: 's4',
        title: 'Indexing',
        body: 'An index trades write cost and storage for read speed. One clustered index defines physical order; secondary indexes point into it. B+ trees dominate because range scans walk the leaf level.',
        points: ['One clustered index per table.', 'B+ tree leaves are linked for range queries.', 'Indexes slow down inserts and updates.'],
      },
    ],
  },
  'operating-systems': {
    generatedAt: '3 days ago',
    keyConcepts: ['Context switch', 'Critical section', 'Safe state', 'Working set', 'Page fault'],
    sections: [
      {
        id: 's1',
        title: 'Processes & Scheduling',
        body: 'A process is a program plus its state; threads split that state so only stack and registers are private. Scheduling policies optimise different metrics, and questions usually ask you to compute average waiting or turnaround time from a Gantt chart.',
        points: ['SJF minimises average waiting time.', 'Round robin bounds response time via the quantum.', 'Context switching is pure overhead.'],
      },
      {
        id: 's2',
        title: 'Synchronisation & Deadlocks',
        body: 'Mutual exclusion, progress and bounded waiting define a correct critical-section solution. Deadlock needs four simultaneous conditions, which gives you four ways to prevent it and a safe-state check to avoid it.',
        points: ['Four conditions: mutual exclusion, hold and wait, no preemption, circular wait.', 'Banker’s algorithm avoids unsafe states.', 'Semaphores can deadlock if ordered carelessly.'],
      },
      {
        id: 's3',
        title: 'Memory Management',
        body: 'Paging removes external fragmentation at the cost of a page table lookup, softened by the TLB. Replacement policy decides fault rate; FIFO can show Belady’s anomaly while stack algorithms cannot.',
        points: ['Effective access time depends on TLB hit ratio.', 'LRU approximates optimal replacement.', 'Thrashing means the working set does not fit.'],
      },
    ],
  },
  'computer-networks': {
    generatedAt: 'Last week',
    keyConcepts: ['Encapsulation', 'Sliding window', 'Congestion window', 'Subnetting', 'Handshake'],
    sections: [
      {
        id: 's1',
        title: 'Layered Models',
        body: 'Each layer adds a header and treats the layer above as payload. Knowing which layer owns a job — addressing, framing, routing, reliability — answers most conceptual questions directly.',
        points: ['Data link frames and detects errors.', 'Network routes between networks.', 'Transport gives end-to-end delivery.'],
      },
      {
        id: 's2',
        title: 'Transport Layer',
        body: 'TCP adds connection setup, ordering, retransmission and flow control over an unreliable network. UDP adds almost nothing, which is exactly why latency-sensitive traffic uses it.',
        points: ['Three-way handshake opens a TCP connection.', 'Sliding window handles flow control.', 'UDP suits voice, video and DNS.'],
      },
      {
        id: 's3',
        title: 'Routing & Congestion',
        body: 'Distance vector shares tables with neighbours and converges slowly; link state floods link costs so every router can run Dijkstra. Congestion control reacts to loss with slow start and congestion avoidance.',
        points: ['Dijkstra needs non-negative weights.', 'Count-to-infinity affects distance vector.', 'Slow start grows the window exponentially.'],
      },
    ],
  },
}

export const getSummaryFor = (materialId) => mockSummaries[materialId]
