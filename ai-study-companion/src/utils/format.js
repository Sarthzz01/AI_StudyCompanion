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
