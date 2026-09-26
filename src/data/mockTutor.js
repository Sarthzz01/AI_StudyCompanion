// Canned tutor answers with source grounding, shaped like a RAG response.
const answers = [
  {
    match: ['binary search tree', 'bst'],
    text: 'A binary search tree is a binary tree with an ordering rule: every key in a node’s left subtree is smaller than the node, and every key in the right subtree is larger.\n\nThat rule is what makes search cheap. At each node you compare once and throw away half the remaining tree, so search, insert and delete all cost O(h) where h is the height. On a balanced tree h is about log n; on a tree built from already-sorted input the tree degenerates into a list and h becomes n.\n\nDeletion is the case worth memorising: a leaf is removed directly, a node with one child is replaced by that child, and a node with two children is replaced by its in-order successor.',
    sources: [
      { label: 'Data Structures.pdf', page: 'Page 12' },
      { label: 'Data Structures.pdf', page: 'Page 15' },
    ],
  },
  {
    match: ['traversal', 'in-order', 'preorder', 'post-order'],
    text: 'Traversals differ only in when the node itself is visited.\n\nPre-order visits the node, then left, then right — useful for copying a tree. In-order visits left, node, right, which on a BST prints the keys in ascending order. Post-order visits both subtrees before the node, which is the safe order for freeing memory. Level-order walks the tree breadth first using a queue.\n\nIf a question gives you two traversals and asks you to rebuild the tree, you need in-order plus one of pre-order or post-order.',
    sources: [{ label: 'Data Structures.pdf', page: 'Page 18' }],
  },
  {
    match: ['graph', 'bfs', 'dfs'],
    text: 'BFS and DFS explore the same graph in different orders.\n\nBFS uses a queue and expands level by level, so the first time it reaches a node it has taken the fewest edges — that is why it solves shortest paths on unweighted graphs. DFS uses a stack or recursion and goes as deep as possible first, which suits cycle detection, topological sorting and connected components.\n\nBoth run in O(V + E) on an adjacency list, and both need a visited set or you will loop forever on a cyclic graph.',
    sources: [
      { label: 'Data Structures.pdf', page: 'Page 64' },
      { label: 'Data Structures.pdf', page: 'Page 67' },
    ],
  },
  {
    match: ['normalisation', 'normalization', 'normal form', '3nf', 'bcnf'],
    text: 'Normal forms remove one kind of redundancy at a time.\n\n1NF asks for atomic values. 2NF removes partial dependencies, so it only matters when the primary key is composite. 3NF removes transitive dependencies — a non-key attribute determined by another non-key attribute. BCNF tightens this: every determinant must be a candidate key.\n\nThe practical method is to start from the functional dependency set, find candidate keys, then check each dependency against the rule for the form you are testing.',
    sources: [{ label: 'DBMS.pdf', page: 'Page 74' }],
  },
  {
    match: ['acid', 'transaction', 'deadlock', 'scheduling'],
    text: 'Think of these guarantees in two groups.\n\nAtomicity and durability are recovery concerns — write-ahead logging lets the system roll back a partial transaction or replay a committed one after a crash. Consistency and isolation are concurrency concerns, enforced by locking protocols such as two-phase locking or by timestamp ordering.\n\nDeadlock needs mutual exclusion, hold and wait, no preemption and circular wait all at once, so breaking any single condition prevents it.',
    sources: [
      { label: 'DBMS.pdf', page: 'Page 131' },
      { label: 'Operating Systems notes', page: 'Page 41' },
    ],
  },
]

const fallback = {
  text: 'Here is how I would approach that.\n\nStart from the definition in your material, then work through one small example by hand before reaching for the general rule — most exam questions test whether you can apply the definition, not recite it.\n\nIf you tell me the specific topic you are stuck on, I can pull the exact section from your uploaded material and walk through it step by step.',
  sources: [{ label: 'Course material', page: 'Multiple sections' }],
}

/** Pick a canned answer based on keywords in the question. */
export function getTutorReply(question) {
  const q = question.toLowerCase()
  const hit = answers.find((a) => a.match.some((keyword) => q.includes(keyword)))
  return hit ? { text: hit.text, sources: hit.sources } : fallback
}

export const suggestedQuestions = [
  'Explain binary search trees.',
  'How do BFS and DFS differ?',
  'Why do we normalise a database?',
  'What guarantees does ACID give?',
]
