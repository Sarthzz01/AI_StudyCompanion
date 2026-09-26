/**
 * Central API service layer for AI Study Companion.
 * Connects frontend pages to the FastAPI backend with JWT authorization.
 * Unmigrated Phase 3 endpoints use mock fallbacks so all pages remain functional.
 */
import axios from 'axios'
import { readStorage, writeStorage, removeStorage } from '../utils/storage.js'
import { mockMaterials, getMaterialById } from '../data/mockMaterials.js'
import { getFlashcardsFor } from '../data/mockFlashcards.js'
import { getSummaryFor } from '../data/mockSummaries.js'
import { buildQuiz, mockPreviousAttempts } from '../data/mockQuiz.js'
import { getTutorReply } from '../data/mockTutor.js'
import { mockProgress } from '../data/mockProgress.js'
import { mockRecommendations } from '../data/mockRecommendations.js'

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const http = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach stored JWT Bearer token
http.interceptors.request.use((config) => {
  const token = readStorage('token', null)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 and extract backend error message
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeStorage('token')
      removeStorage('user')
    }
    const message = error.response?.data?.detail || error.message || 'A network error occurred'
    return Promise.reject(new Error(message))
  }
)

const delay = (ms = 400) => new Promise((resolve) => setTimeout(resolve, ms))

/* ---------------------------------- auth ---------------------------------- */

export async function loginUser({ email, password }) {
  const { data } = await http.post('/auth/login', { email, password })
  if (data.access_token) {
    writeStorage('token', data.access_token)
  }
  return data.user
}

export async function signupUser({ name, email, password }) {
  const { data } = await http.post('/auth/register', { name, email, password })
  if (data.access_token) {
    writeStorage('token', data.access_token)
  }
  return data.user
}

export async function logoutUser() {
  try {
    await http.post('/auth/logout')
  } catch {
    /* ignore logout error */
  } finally {
    removeStorage('token')
    removeStorage('user')
  }
}

export async function getCurrentUser() {
  const { data } = await http.get('/auth/me')
  return data
}

/* -------------------------------- profile --------------------------------- */

export async function getProfile() {
  const { data } = await http.get('/profile')
  return data
}

export async function updateProfile(changes) {
  const { data } = await http.put('/profile', changes)
  return data
}

export async function changeUserPassword({ current_password, new_password }) {
  const { data } = await http.put('/profile/password', { current_password, new_password })
  return data
}

/* -------------------------------- subjects -------------------------------- */

export async function getSubjects() {
  const { data } = await http.get('/subjects')
  return data
}

export async function getSubjectTopics(subjectId) {
  const { data } = await http.get(`/subjects/${subjectId}/topics`)
  return data
}

/* -------------------------------- materials -------------------------------- */

export async function getMaterials() {
  try {
    const { data } = await http.get('/materials')
    return data
  } catch (err) {
    console.warn('Backend /materials fetch failed, falling back to mock catalogue:', err.message)
    return mockMaterials
  }
}

export async function getMaterial(id) {
  try {
    const { data } = await http.get(`/materials/${id}`)
    return data
  } catch (err) {
    const fallback = getMaterialById(id)
    if (fallback) return fallback
    throw err
  }
}

export async function uploadMaterial({ title, type, file, description, pages, onUploadProgress }) {
  if (file) {
    const formData = new FormData()
    if (title) formData.append('title', title)
    if (type) formData.append('type', type)
    if (description) formData.append('description', description)
    if (pages) formData.append('pages', pages)
    formData.append('file', file)

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
    if (typeof onUploadProgress === 'function') {
      config.onUploadProgress = onUploadProgress
    }

    try {
      const { data } = await http.post('/materials/upload', formData, config)
      return data
    } catch {
      // Fallback to general materials endpoint
      const { data } = await http.post('/materials', formData, config)
      return data
    }
  }

  const { data } = await http.post('/materials', {
    title: title || 'Untitled material',
    type: type || 'PDF',
    description: description || 'Uploaded study material.',
    pages: pages || 1,
  })
  return data
}

export async function deleteMaterial(id) {
  const { data } = await http.delete(`/materials/${id}`)
  return data
}

/* ------------------------------- ai features ------------------------------- */

export async function askTutor({ message, question, materialId, material_id, history, conversationId, conversation_id }) {
  const queryText = (message || question || '').trim()
  const payload = {
    message: queryText,
    question: queryText,
  }
  if (history && Array.isArray(history)) {
    payload.history = history
  }
  if (materialId && materialId !== 'general') {
    payload.materialId = materialId
    payload.material_id = materialId
  }
  const convId = conversationId || conversation_id
  if (convId) {
    payload.conversationId = convId
    payload.conversation_id = convId
  }

  try {
    const { data } = await http.post('/tutor/ask', payload)
    return {
      answer: data.answer,
      sources: data.sources || [],
      grounded: Boolean(data.grounded),
      model: data.model,
      conversation_id: data.conversation_id,
      title: data.title,
    }
  } catch (err) {
    console.warn('Backend /tutor/ask failed, falling back to educational assistant:', err.message)
    const reply = getTutorReply(queryText)
    return {
      answer: reply?.text || 'I am ready to help you with your studies. Please try asking your question again.',
      sources: reply?.sources || [],
      grounded: true,
      conversation_id: convId || `local_${Date.now()}`,
      title: queryText.slice(0, 30),
    }
  }
}

export async function getTutorConversations() {
  try {
    const { data } = await http.get('/tutor/conversations')
    return Array.isArray(data) ? data : []
  } catch (err) {
    console.warn('Could not load tutor conversations:', err.message)
    return []
  }
}

export async function getTutorConversation(conversationId) {
  try {
    const { data } = await http.get(`/tutor/conversations/${conversationId}`)
    return Array.isArray(data) ? data : []
  } catch (err) {
    console.warn(`Could not load conversation ${conversationId}:`, err.message)
    return []
  }
}

export async function deleteTutorConversation(conversationId) {
  try {
    await http.delete(`/tutor/conversations/${conversationId}`)
    return true
  } catch (err) {
    console.warn(`Could not delete conversation ${conversationId}:`, err.message)
    throw err
  }
}

export async function renameTutorConversation(conversationId, title) {
  try {
    const { data } = await http.patch(`/tutor/conversations/${conversationId}/rename`, { title })
    return data
  } catch (err) {
    console.warn(`Could not rename conversation ${conversationId}:`, err.message)
    throw err
  }
}

export async function getTutorHistory(materialId) {
  try {
    const params = {}
    if (materialId && materialId !== 'general') params.material_id = materialId
    const { data } = await http.get('/tutor/history', { params })
    return data
  } catch (err) {
    console.warn('Could not load tutor history from backend:', err.message)
    return []
  }
}

export async function generateSummary(materialId) {
  const targetMatId = materialId || 'data-structures'
  try {
    const { data } = await http.get(`/summaries/${targetMatId}`)
    return data
  } catch (err) {
    console.warn(`Backend GET /summaries/${targetMatId} failed, trying POST /summaries/generate or mock fallback:`, err.message)
    try {
      const { data } = await http.post('/summaries/generate', {
        materialId: targetMatId,
        material_id: targetMatId,
      })
      return data
    } catch {
      const summary = getSummaryFor(targetMatId)
      if (!summary) throw new Error('No summary is available for this material yet.')
      return summary
    }
  }
}

export async function getSummaries() {
  try {
    const { data } = await http.get('/summaries')
    return data
  } catch (err) {
    console.warn('Backend /summaries failed:', err.message)
    return []
  }
}

/* ------------------------------- flashcards ------------------------------- */

export async function getFlashcards(materialId, topic) {
  try {
    const params = { materialId }
    if (topic && topic !== 'All topics') params.topic = topic
    const { data } = await http.get('/flashcards', { params })
    if (data && data.length > 0) {
      return data.map((item) => ({
        id: item.id,
        topic: item.topic_name || item.topic || 'General',
        front: item.front,
        back: item.back,
        difficulty: item.difficulty,
        source: item.source || 'Study Material',
      }))
    }
  } catch (err) {
    console.warn('Backend /flashcards fetch failed, attempting mock fallback:', err.message)
  }
  return getFlashcardsFor(materialId)
}

export async function generateFlashcards({ materialId, topic, count, difficulty }) {
  try {
    const { data } = await http.post('/flashcards/generate', {
      materialId,
      topic: topic && topic !== 'All topics' ? topic : undefined,
      count: count || 5,
      difficulty: difficulty || 'medium',
    })
    return data.map((item) => ({
      id: item.id,
      topic: item.topic_name || item.topic || 'General',
      front: item.front,
      back: item.back,
      difficulty: item.difficulty,
      source: item.source || 'Study Material',
    }))
  } catch (err) {
    console.warn('Backend /flashcards/generate failed:', err.message)
    throw err
  }
}

export async function recordFlashcardReview(cardId, rating) {
  if (typeof cardId === 'number') {
    try {
      const { data } = await http.post(`/flashcards/${cardId}/review`, { rating })
      return data
    } catch (err) {
      console.warn(`Backend /flashcards/${cardId}/review failed:`, err.message)
    }
  }
  return { success: true }
}

/* ---------------------------------- quiz ---------------------------------- */

export async function generateQuiz({ materialId, topic, difficulty, count }) {
  try {
    const { data: quiz } = await http.post('/quizzes/generate', {
      materialId,
      topic: topic || 'All topics',
      difficulty: difficulty || 'mixed',
      count: Number(count) || 5,
    })

    // Start an active attempt for this quiz
    const { data: attempt } = await http.post(`/quizzes/${quiz.id}/attempt`)

    const questions = attempt.questions.map((q) => ({
      id: q.id,
      question: q.question,
      topic: q.topic,
      options: q.options,
      difficulty: q.difficulty,
      attemptId: attempt.id,
      quizId: quiz.id,
    }))

    // Attach metadata to the questions array
    questions.attemptId = attempt.id
    questions.quizId = quiz.id
    return questions
  } catch (err) {
    console.warn('Backend quiz generation failed, falling back to client quiz builder:', err.message)
    const questions = buildQuiz({ materialId, topic, difficulty, count })
    if (!questions.length) throw new Error('No questions exist for that combination yet.')
    return questions
  }
}

export async function submitQuiz(payload) {
  const attemptId = payload.attemptId || (typeof payload.id === 'number' || (typeof payload.id === 'string' && !payload.id.startsWith('attempt-')) ? payload.id : null)

  if (attemptId) {
    try {
      const answersPayload = (payload.review || []).map((r) => ({
        question_id: r.id,
        selected_option: r.selected,
      }))

      const { data } = await http.post(`/quiz-attempts/${attemptId}/submit`, {
        answers: answersPayload,
      })
      return data
    } catch (err) {
      console.warn('Backend quiz submit failed, using client computed attempt:', err.message)
    }
  }
  await delay(400)
  return payload
}

export async function getQuizAttempts(materialId) {
  try {
    const { data } = await http.get('/quiz-attempts', { params: { materialId } })
    if (data && Array.isArray(data)) {
      return data.map((a) => ({
        id: a.id,
        quizId: a.quiz_id,
        materialId: a.material_id,
        materialTitle: a.material_title,
        topic: a.topic,
        score: a.score,
        total: a.total,
        accuracy: a.accuracy,
        date: a.date,
        difficulty: a.difficulty,
      }))
    }
  } catch (err) {
    console.warn('Backend /quiz-attempts fetch failed:', err.message)
  }
  return []
}

export async function getQuizAttempt(id) {
  const { data } = await http.get(`/quiz-attempts/${id}`)
  return data
}

/* -------------------------- progress & suggestions ------------------------- */

export async function getProgress() {
  try {
    const { data } = await http.get('/progress')
    if (data && data.stats) {
      return data
    }
  } catch (err) {
    console.warn('Backend /progress fetch failed:', err.message)
  }
  return null
}

export async function getTopicProgress() {
  try {
    const { data } = await http.get('/progress/topics')
    return data
  } catch (err) {
    console.warn('Backend /progress/topics failed:', err.message)
    return []
  }
}

export async function getLearnerModel() {
  try {
    const { data } = await http.get('/learner-model')
    return data
  } catch (err) {
    console.warn('Backend /learner-model failed:', err.message)
    return null
  }
}

export async function getTopicLearnerModel(topicId) {
  const { data } = await http.get(`/learner-model/${encodeURIComponent(topicId)}`)
  return data
}

/* ----------------------------- study sessions ----------------------------- */

export async function logStudySession({ duration_minutes, session_type, material_id, topic }) {
  try {
    const { data } = await http.post('/study-sessions', {
      duration_minutes: Number(duration_minutes) || 15,
      session_type: session_type || 'reading',
      material_id: material_id || null,
      topic: topic || null,
    })
    return data
  } catch (err) {
    console.warn('Backend /study-sessions post failed:', err.message)
    return null
  }
}

export async function getStudySessions() {
  try {
    const { data } = await http.get('/study-sessions')
    return data
  } catch (err) {
    console.warn('Backend /study-sessions fetch failed:', err.message)
    return []
  }
}

/* ---------------------------------- goals --------------------------------- */

export async function getGoals() {
  try {
    const { data } = await http.get('/goals')
    if (data && data.length > 0) {
      return data
    }
  } catch (err) {
    console.warn('Backend /goals fetch failed:', err.message)
  }
  return null
}

export async function createGoal(goal) {
  try {
    const { data } = await http.post('/goals', goal)
    return data
  } catch (err) {
    console.warn('Backend /goals post failed:', err.message)
    return { id: `g-${Date.now()}`, current: 0, completed: false, ...goal }
  }
}

export async function updateGoal(id, updates) {
  if (typeof id === 'number') {
    try {
      const { data } = await http.put(`/goals/${id}`, updates)
      return data
    } catch (err) {
      console.warn(`Backend PUT /goals/${id} failed:`, err.message)
    }
  }
  return updates
}

export async function deleteGoal(id) {
  if (typeof id === 'number') {
    try {
      await http.delete(`/goals/${id}`)
      return true
    } catch (err) {
      console.warn(`Backend DELETE /goals/${id} failed:`, err.message)
    }
  }
  return true
}

export async function getRecommendations() {
  try {
    const { data } = await http.get('/recommendations')
    if (data && Array.isArray(data) && data.length > 0) {
      return data
    }
  } catch (err) {
    console.warn('Backend /recommendations fetch failed:', err.message)
  }
  return mockRecommendations
}

export async function getTodayRecommendations() {
  try {
    const { data } = await http.get('/recommendations/today')
    if (data && data.recommendations) {
      return data
    }
  } catch (err) {
    console.warn('Backend /recommendations/today fetch failed:', err.message)
  }
  return {
    date: new Date().toISOString().slice(0, 10),
    recommendations: mockRecommendations,
    ai_study_tip: null,
    total_pending_revisions: 0,
  }
}

/* -------------------------- study plan & revision -------------------------- */

export async function getStudyPlan(targetMinutes = 60, force = false) {
  try {
    const { data } = await http.get('/study-plan', {
      params: { target_minutes: targetMinutes, force }
    })
    return data
  } catch (err) {
    console.warn('Backend /study-plan fetch failed:', err.message)
    return {
      date: new Date().toISOString().slice(0, 10),
      target_minutes: targetMinutes,
      allocated_minutes: 60,
      completed_minutes: 0,
      completion_rate: 0,
      total_tasks: 3,
      completed_tasks: 0,
      tasks: [
        {
          id: 1,
          task_title: 'Review Page Replacement Algorithms',
          topic: 'Page Replacement',
          material_id: null,
          activity: 'flashcards',
          duration_minutes: 15,
          priority: 'HIGH',
          difficulty: 'MEDIUM',
          completed: false,
          completed_at: null,
          reason: 'Scheduled spaced repetition review due today',
          action_url: '/flashcards',
          order_index: 0
        },
        {
          id: 2,
          task_title: 'Practice Paging & Address Translation',
          topic: 'Paging',
          material_id: null,
          activity: 'quiz',
          duration_minutes: 25,
          priority: 'HIGH',
          difficulty: 'HARD',
          completed: false,
          completed_at: null,
          reason: 'Weak mastery topic requiring remediation',
          action_url: '/quiz',
          order_index: 1
        },
        {
          id: 3,
          task_title: 'AI Tutor Deep Dive: Virtual Memory Concepts',
          topic: 'Virtual Memory',
          material_id: null,
          activity: 'tutor',
          duration_minutes: 20,
          priority: 'MEDIUM',
          difficulty: 'MEDIUM',
          completed: false,
          completed_at: null,
          reason: 'Solidify foundational concepts',
          action_url: '/tutor',
          order_index: 2
        }
      ],
      ai_guidance: 'Focus on Page Replacement and Paging today to boost your recall before tomorrow.',
      due_revisions_count: 1
    }
  }
}

export async function completeStudyPlanTask(taskId) {
  try {
    const { data } = await http.post(`/study-plan/${taskId}/complete`)
    return data
  } catch (err) {
    console.warn(`Backend POST /study-plan/${taskId}/complete failed:`, err.message)
    return { id: taskId, completed: true, completed_at: new Date().toISOString() }
  }
}

export async function getRevisions() {
  try {
    const { data } = await http.get('/revision')
    return data
  } catch (err) {
    console.warn('Backend /revision fetch failed:', err.message)
    return []
  }
}

export async function getDueRevisions() {
  try {
    const { data } = await http.get('/revision/due')
    return data
  } catch (err) {
    console.warn('Backend /revision/due fetch failed:', err.message)
    return {
      date: new Date().toISOString().slice(0, 10),
      total_due: 0,
      revisions: []
    }
  }
}

/* ---------------------------------- viva ---------------------------------- */

export async function startVivaSession({ topic, mode = 'basic', difficulty = 'medium', material_id = null, total_questions = 4 }) {
  try {
    const { data } = await http.post('/viva/start', {
      topic,
      mode,
      difficulty,
      material_id,
      total_questions
    })
    return data
  } catch (err) {
    console.warn('Backend /viva/start failed:', err.message)
    throw err
  }
}

export async function submitVivaAnswer(sessionId, { question_id, answer_text }) {
  try {
    const { data } = await http.post(`/viva/${sessionId}/answer`, {
      question_id,
      answer_text
    })
    return data
  } catch (err) {
    console.warn(`Backend /viva/${sessionId}/answer failed:`, err.message)
    throw err
  }
}

export async function endVivaSession(sessionId) {
  try {
    const { data } = await http.post(`/viva/${sessionId}/end`)
    return data
  } catch (err) {
    console.warn(`Backend /viva/${sessionId}/end failed:`, err.message)
    throw err
  }
}

export async function getVivaSession(sessionId) {
  try {
    const { data } = await http.get(`/viva/${sessionId}`)
    return data
  } catch (err) {
    console.warn(`Backend /viva/${sessionId} failed:`, err.message)
    throw err
  }
}

export async function getVivaHistory() {
  try {
    const { data } = await http.get('/viva/history')
    return data
  } catch (err) {
    console.warn('Backend /viva/history failed:', err.message)
    return { total_sessions: 0, average_score: 0, sessions: [] }
  }
}

/* ---------------------------------- instructor module ---------------------------------- */

export async function getInstructorDashboard() {
  try {
    const { data } = await http.get('/instructor/dashboard')
    return data
  } catch (err) {
    console.warn('Backend /instructor/dashboard failed:', err.message)
    throw err
  }
}

export async function getInstructorStudents() {
  try {
    const { data } = await http.get('/instructor/students')
    return data
  } catch (err) {
    console.warn('Backend /instructor/students failed:', err.message)
    throw err
  }
}

export async function getInstructorStudentDetail(studentId) {
  try {
    const { data } = await http.get(`/instructor/students/${studentId}`)
    return data
  } catch (err) {
    console.warn(`Backend /instructor/students/${studentId} failed:`, err.message)
    throw err
  }
}

export async function getInstructorAssessments() {
  try {
    const { data } = await http.get('/instructor/assessments')
    return data
  } catch (err) {
    console.warn('Backend /instructor/assessments failed:', err.message)
    throw err
  }
}

export async function createInstructorAssessment(payload) {
  try {
    const { data } = await http.post('/instructor/assessments', payload)
    return data
  } catch (err) {
    console.warn('Backend POST /instructor/assessments failed:', err.message)
    throw err
  }
}

export async function getInstructorAssessment(assessmentId) {
  try {
    const { data } = await http.get(`/instructor/assessments/${assessmentId}`)
    return data
  } catch (err) {
    console.warn(`Backend /instructor/assessments/${assessmentId} failed:`, err.message)
    throw err
  }
}

export async function updateInstructorAssessment(assessmentId, payload) {
  try {
    const { data } = await http.put(`/instructor/assessments/${assessmentId}`, payload)
    return data
  } catch (err) {
    console.warn(`Backend PUT /instructor/assessments/${assessmentId} failed:`, err.message)
    throw err
  }
}

export async function deleteInstructorAssessment(assessmentId) {
  try {
    const { data } = await http.delete(`/instructor/assessments/${assessmentId}`)
    return data
  } catch (err) {
    console.warn(`Backend DELETE /instructor/assessments/${assessmentId} failed:`, err.message)
    throw err
  }
}

export async function assignInstructorAssessment(assessmentId, payload) {
  try {
    const { data } = await http.post(`/instructor/assessments/${assessmentId}/assign`, payload)
    return data
  } catch (err) {
    console.warn(`Backend POST /instructor/assessments/${assessmentId}/assign failed:`, err.message)
    throw err
  }
}

export async function getInstructorAssignments() {
  try {
    const { data } = await http.get('/instructor/assignments')
    return data
  } catch (err) {
    console.warn('Backend /instructor/assignments failed:', err.message)
    throw err
  }
}

export async function getClassAnalyticsOverview() {
  try {
    const { data } = await http.get('/instructor/analytics/overview')
    return data
  } catch (err) {
    console.warn('Backend /instructor/analytics/overview failed:', err.message)
    throw err
  }
}

export async function getClassSummaryReport() {
  try {
    const { data } = await http.get('/instructor/reports/class-summary')
    return data
  } catch (err) {
    console.warn('Backend /instructor/reports/class-summary failed:', err.message)
    throw err
  }
}

export async function getInstructorFeedbacks(studentId = null) {
  try {
    const params = studentId ? { student_id: studentId } : {}
    const { data } = await http.get('/instructor/feedback', { params })
    return data
  } catch (err) {
    console.warn('Backend /instructor/feedback failed:', err.message)
    throw err
  }
}

export async function createInstructorFeedback(payload) {
  try {
    const { data } = await http.post('/instructor/feedback', payload)
    return data
  } catch (err) {
    console.warn('Backend POST /instructor/feedback failed:', err.message)
    throw err
  }
}

export async function aiGenerateAssessmentQuestions(payload) {
  try {
    const { data } = await http.post('/instructor/ai/generate-questions', payload)
    return data
  } catch (err) {
    console.warn('Backend POST /instructor/ai/generate-questions failed:', err.message)
    throw err
  }
}

/* ---------------------------------- student assessment taker ---------------------------------- */

export async function getAssignedAssessments() {
  try {
    const { data } = await http.get('/assessments/assigned')
    return data
  } catch (err) {
    console.warn('Backend /assessments/assigned failed:', err.message)
    return []
  }
}

export async function getAssessmentForStudent(assessmentId) {
  try {
    const { data } = await http.get(`/assessments/${assessmentId}`)
    return data
  } catch (err) {
    console.warn(`Backend /assessments/${assessmentId} failed:`, err.message)
    throw err
  }
}

export async function submitStudentAssessment(assessmentId, payload) {
  try {
    const { data } = await http.post(`/assessments/${assessmentId}/submit`, payload)
    return data
  } catch (err) {
    console.warn(`Backend POST /assessments/${assessmentId}/submit failed:`, err.message)
    throw err
  }
}

/* ---------------------------------- notifications ---------------------------------- */

export async function getNotifications(unreadOnly = false) {
  try {
    const params = unreadOnly ? { unread_only: true } : {}
    const { data } = await http.get('/notifications', { params })
    return data
  } catch (err) {
    console.warn('Backend /notifications failed:', err.message)
    return []
  }
}

export async function getNotificationsSummary() {
  try {
    const { data } = await http.get('/notifications/summary')
    return data
  } catch (err) {
    console.warn('Backend /notifications/summary failed:', err.message)
    return { notifications: [], unread_count: 0, total_count: 0 }
  }
}

export async function createNotification(payload) {
  try {
    const { data } = await http.post('/notifications', payload)
    return data
  } catch (err) {
    console.warn('Backend POST /notifications failed:', err.message)
    throw err
  }
}

export async function markNotificationRead(id) {
  try {
    const { data } = await http.put(`/notifications/${id}/read`)
    return data
  } catch (err) {
    console.warn(`Backend PUT /notifications/${id}/read failed:`, err.message)
    throw err
  }
}

export async function markAllNotificationsRead() {
  try {
    const { data } = await http.put('/notifications/read-all')
    return data
  } catch (err) {
    console.warn('Backend PUT /notifications/read-all failed:', err.message)
    throw err
  }
}

export async function deleteNotification(id) {
  try {
    await http.delete(`/notifications/${id}`)
  } catch (err) {
    console.warn(`Backend DELETE /notifications/${id} failed:`, err.message)
    throw err
  }
}

export async function clearAllNotifications() {
  try {
    await http.delete('/notifications')
  } catch (err) {
    console.warn('Backend DELETE /notifications failed:', err.message)
    throw err
  }
}

