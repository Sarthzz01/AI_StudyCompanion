import { Network, GitBranch, ListOrdered, Layers } from 'lucide-react'

// Recommendations the personalisation engine would produce from the learner model.
export const mockRecommendations = [
  {
    id: 'r1',
    title: 'Practice Graph Traversal',
    reason: 'Accuracy is 44% — your lowest topic this week.',
    action: 'Start practice quiz',
    to: '/quizzes',
    icon: Network,
    priority: 'high',
  },
  {
    id: 'r2',
    title: 'Review Binary Trees',
    reason: 'You answered 3 of 5 tree questions correctly in your last attempt.',
    action: 'Open flashcards',
    to: '/flashcards',
    icon: GitBranch,
    priority: 'medium',
  },
  {
    id: 'r3',
    title: 'Take a Sorting quiz',
    reason: 'It has been 6 days since you practised sorting algorithms.',
    action: 'Start quiz',
    to: '/quizzes',
    icon: ListOrdered,
    priority: 'medium',
  },
  {
    id: 'r4',
    title: 'Read the Normalisation summary',
    reason: 'Normalisation is the weakest topic in DBMS at 41%.',
    action: 'Open summary',
    to: '/summaries',
    icon: Layers,
    priority: 'low',
  },
]
