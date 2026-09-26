// Seed analytics for the student. The StudyDataContext updates a copy of this after each quiz.
export const mockProgress = {
  stats: {
    accuracy: 76,
    questionsAttempted: 148,
    studyMinutes: 615,
    topicsCompleted: 11,
    totalTopics: 27,
    overallProgress: 58,
  },
  performanceOverTime: [
    { date: 'Sep 01', accuracy: 58 },
    { date: 'Sep 04', accuracy: 63 },
    { date: 'Sep 07', accuracy: 61 },
    { date: 'Sep 10', accuracy: 70 },
    { date: 'Sep 13', accuracy: 74 },
    { date: 'Sep 15', accuracy: 80 },
  ],
  topicAccuracy: [
    { topic: 'Tree Traversal', accuracy: 92 },
    { topic: 'SQL Queries', accuracy: 84 },
    { topic: 'CPU Scheduling', accuracy: 78 },
    { topic: 'Sorting', accuracy: 71 },
    { topic: 'BST Operations', accuracy: 52 },
    { topic: 'Graph Traversal', accuracy: 44 },
    { topic: 'Normalisation', accuracy: 41 },
  ],
  weeklyStudy: [
    { day: 'Mon', minutes: 65 },
    { day: 'Tue', minutes: 90 },
    { day: 'Wed', minutes: 45 },
    { day: 'Thu', minutes: 120 },
    { day: 'Fri', minutes: 70 },
    { day: 'Sat', minutes: 140 },
    { day: 'Sun', minutes: 85 },
  ],
  recentlyImproved: [
    { topic: 'Tree Traversal', change: 18 },
    { topic: 'SQL Queries', change: 12 },
    { topic: 'CPU Scheduling', change: 9 },
  ],
}
