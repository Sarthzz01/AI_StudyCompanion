export function formatMinutes(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (!h) return `${m}m`
  return m ? `${h}h ${m}m` : `${h}h`
}

export function todayLabel(date = new Date()) {
  return date.toLocaleDateString(undefined, { month: 'short', day: '2-digit' })
}

export function clamp(value, min = 0, max = 100) {
  return Math.min(max, Math.max(min, value))
}

export function formatRelativeTime(value) {
  if (!value) return 'Not studied yet'
  if (typeof value === 'string') {
    const clean = value.trim()
    // If it's an ISO timestamp or date format string
    if (!clean.includes(' ') || clean.includes('T')) {
      const parsed = new Date(clean)
      if (!isNaN(parsed.getTime())) {
        const diffMs = Date.now() - parsed.getTime()
        const diffSec = Math.max(0, Math.floor(diffMs / 1000))
        if (diffSec < 60) return 'Just now'
        const diffMin = Math.floor(diffSec / 60)
        if (diffMin < 60) return `${diffMin}m ago`
        const diffHours = Math.floor(diffMin / 60)
        if (diffHours < 24) return `${diffHours}h ago`
        const diffDays = Math.floor(diffHours / 24)
        if (diffDays === 1) return 'Yesterday'
        if (diffDays < 7) return `${diffDays}d ago`
        if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
        return parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      }
    }
    return clean
  }
  if (value instanceof Date) {
    const diffMs = Date.now() - value.getTime()
    const diffSec = Math.max(0, Math.floor(diffMs / 1000))
    if (diffSec < 60) return 'Just now'
    const diffMin = Math.floor(diffSec / 60)
    if (diffMin < 60) return `${diffMin}m ago`
    const diffHours = Math.floor(diffMin / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
    return value.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  }
  return String(value)
}
