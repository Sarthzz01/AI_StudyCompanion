import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react'
import { readStorage, writeStorage, removeStorage } from '../utils/storage.js'
import {
  getProgress,
  getQuizAttempts,
  getGoals,
  createGoal,
  updateGoal,
  deleteGoal,
  getNotifications,
  markNotificationRead as apiMarkNotificationRead,
  markAllNotificationsRead as apiMarkAllNotificationsRead,
  clearAllNotifications as apiClearAllNotifications,
  createNotification as apiCreateNotification,
} from '../services/api.js'
import { useAuth } from './AuthContext.jsx'

export const defaultProgress = {
  stats: {
    accuracy: 0,
    questionsAttempted: 0,
    studyMinutes: 0,
    topicsCompleted: 0,
    totalTopics: 0,
    overallProgress: 0,
    flashcardPerformance: 0,
    recallReliability: 50,
    averageMastery: 0,
  },
  performanceOverTime: [],
  topicAccuracy: [],
  weeklyStudy: [
    { day: 'Mon', minutes: 0 },
    { day: 'Tue', minutes: 0 },
    { day: 'Wed', minutes: 0 },
    { day: 'Thu', minutes: 0 },
    { day: 'Fri', minutes: 0 },
    { day: 'Sat', minutes: 0 },
    { day: 'Sun', minutes: 0 },
  ],
  recentlyImproved: [],
  strongTopics: [],
  weakTopics: [],
  topicsNeedingReview: [],
}

/**
 * Holds real student progress, quiz attempts, goals, and notifications.
 * Automatically synchronizes with the backend with per-user isolation.
 */
const StudyDataContext = createContext(null)

export function StudyDataProvider({ children }) {
  const { user, isAuthenticated } = useAuth()
  const userId = user?.id || null

  const [progress, setProgress] = useState(() => {
    if (userId) return readStorage(`progress:${userId}`, defaultProgress)
    return defaultProgress
  })
  const [attempts, setAttempts] = useState(() => {
    if (userId) return readStorage(`attempts:${userId}`, [])
    return []
  })
  const [goals, setGoals] = useState(() => {
    if (userId) return readStorage(`goals:${userId}`, [])
    return []
  })
  const [notifications, setNotifications] = useState(() => {
    if (userId) return readStorage(`notifications:${userId}`, [])
    return []
  })

  // Synchronize progress and attempts from backend
  const refreshProgress = useCallback(async () => {
    if (!isAuthenticated && !readStorage('token', null)) return null
    try {
      const [p, a] = await Promise.all([getProgress(), getQuizAttempts()])
      if (p && p.stats) {
        setProgress(p)
        if (userId) writeStorage(`progress:${userId}`, p)
      }
      if (a && Array.isArray(a)) {
        setAttempts(a)
        if (userId) writeStorage(`attempts:${userId}`, a)
      }
      return { progress: p, attempts: a }
    } catch (err) {
      console.warn('refreshProgress error:', err.message)
      return null
    }
  }, [isAuthenticated, userId])

  // Synchronize goals from backend
  const refreshGoals = useCallback(async () => {
    if (!isAuthenticated && !readStorage('token', null)) return
    try {
      const g = await getGoals()
      if (g && Array.isArray(g)) {
        setGoals(g)
        if (userId) writeStorage(`goals:${userId}`, g)
      }
    } catch (err) {
      console.warn('refreshGoals error:', err.message)
    }
  }, [isAuthenticated, userId])

  // Synchronize notifications from backend
  const refreshNotifications = useCallback(async () => {
    if (!isAuthenticated && !readStorage('token', null)) return
    try {
      const notifs = await getNotifications()
      if (notifs && Array.isArray(notifs)) {
        setNotifications(notifs)
        if (userId) writeStorage(`notifications:${userId}`, notifs)
      }
    } catch (err) {
      console.warn('refreshNotifications error:', err.message)
    }
  }, [isAuthenticated, userId])

  // React to login / logout / user changes
  useEffect(() => {
    if (isAuthenticated && userId) {
      // Load cached user data first for fast render
      const cachedProgress = readStorage(`progress:${userId}`, defaultProgress)
      const cachedAttempts = readStorage(`attempts:${userId}`, [])
      const cachedGoals = readStorage(`goals:${userId}`, [])
      const cachedNotifs = readStorage(`notifications:${userId}`, [])

      setProgress(cachedProgress)
      setAttempts(cachedAttempts)
      setGoals(cachedGoals)
      setNotifications(cachedNotifs)

      // Fetch live data from backend for this authenticated student
      refreshProgress()
      refreshGoals()
      refreshNotifications()
    } else {
      // Clean reset on logout
      setProgress(defaultProgress)
      setAttempts([])
      setGoals([])
      setNotifications([])
    }
  }, [isAuthenticated, userId, refreshProgress, refreshGoals, refreshNotifications])

  // Persist user-isolated state
  useEffect(() => {
    if (userId) writeStorage(`progress:${userId}`, progress)
  }, [progress, userId])

  useEffect(() => {
    if (userId) writeStorage(`attempts:${userId}`, attempts)
  }, [attempts, userId])

  useEffect(() => {
    if (userId) writeStorage(`goals:${userId}`, goals)
  }, [goals, userId])

  useEffect(() => {
    if (userId) writeStorage(`notifications:${userId}`, notifications)
  }, [notifications, userId])

  /* ------------------------------ notifications ----------------------------- */

  const pushNotification = async (notification) => {
    const tempId = typeof notification.id === 'number' ? notification.id : Date.now()
    const newNotif = {
      id: tempId,
      time: 'Just now',
      read: false,
      title: notification.title || 'Notification',
      body: notification.body || notification.message || '',
      type: notification.type || 'info',
      ...notification,
    }
    setNotifications((list) => [newNotif, ...list])

    try {
      const serverNotif = await apiCreateNotification({
        title: newNotif.title,
        message: newNotif.body,
        type: newNotif.type,
      })
      if (serverNotif && serverNotif.id) {
        setNotifications((list) => list.map((n) => (n.id === tempId ? serverNotif : n)))
      }
    } catch {
      /* keep local fallback */
    }
  }

  const markNotificationRead = async (id) => {
    setNotifications((list) => list.map((n) => (n.id === id ? { ...n, read: true } : n)))
    if (typeof id === 'number') {
      try {
        await apiMarkNotificationRead(id)
      } catch {
        /* keep local */
      }
    }
  }

  const markAllNotificationsRead = async () => {
    setNotifications((list) => list.map((n) => ({ ...n, read: true })))
    try {
      await apiMarkAllNotificationsRead()
    } catch {
      /* keep local */
    }
  }

  const clearNotifications = async () => {
    setNotifications([])
    if (userId) removeStorage(`notifications:${userId}`)
    try {
      await apiClearAllNotifications()
    } catch {
      /* keep local */
    }
  }

  const unreadCount = useMemo(() => notifications.filter((n) => !n.read).length, [notifications])

  /* ---------------------------------- goals --------------------------------- */

  const addGoal = async (goal) => {
    const tempId = `g-${Date.now()}`
    const localGoal = { id: tempId, current: 0, completed: false, ...goal }
    setGoals((list) => [localGoal, ...list])

    try {
      const serverGoal = await createGoal(goal)
      if (serverGoal && serverGoal.id) {
        setGoals((list) => list.map((g) => (g.id === tempId ? serverGoal : g)))
      }
    } catch {
      /* keep local */
    }
  }

  const completeGoal = async (id) => {
    let completedTitle = ''
    setGoals((list) =>
      list.map((g) => {
        if (g.id !== id) return g
        completedTitle = g.title
        return { ...g, completed: true, current: g.target }
      })
    )

    if (completedTitle) {
      pushNotification({
        type: 'goal',
        title: 'Study goal completed',
        body: `${completedTitle} is done. Nice work.`,
      })
    }

    try {
      await updateGoal(id, { completed: true })
    } catch {
      /* keep local */
    }
  }

  const removeGoal = async (id) => {
    setGoals((list) => list.filter((g) => g.id !== id))
    try {
      await deleteGoal(id)
    } catch {
      /* keep local */
    }
  }

  /* -------------------------------- quiz data ------------------------------- */

  /**
   * Record a finished quiz: store the attempt, refresh the authoritative analytics
   * used by the Progress page, and refresh notifications.
   */
  const recordQuizAttempt = async (attempt) => {
    // Optimistically update attempt history
    setAttempts((list) => {
      const filtered = list.filter((a) => String(a.id) !== String(attempt.id))
      return [attempt, ...filtered]
    })

    // Fetch authoritative progress and notifications recalculation from backend
    await Promise.all([refreshProgress(), refreshNotifications()])
  }

  const lastAttempt = attempts[0] || null

  const resetProgress = async () => {
    await refreshProgress()
  }

  return (
    <StudyDataContext.Provider
      value={{
        progress,
        attempts,
        lastAttempt,
        recordQuizAttempt,
        refreshProgress,
        resetProgress,
        goals,
        addGoal,
        completeGoal,
        removeGoal,
        notifications,
        unreadCount,
        pushNotification,
        markNotificationRead,
        markAllNotificationsRead,
        clearNotifications,
      }}
    >
      {children}
    </StudyDataContext.Provider>
  )
}

export function useStudyData() {
  const ctx = useContext(StudyDataContext)
  if (!ctx) throw new Error('useStudyData must be used inside StudyDataProvider')
  return ctx
}
