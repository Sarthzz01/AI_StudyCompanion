// Thin localStorage wrapper so a failure (private mode, quota) never crashes the app.
const PREFIX = 'asc:'

export function readStorage(key, fallback) {
  try {
    const raw = window.localStorage.getItem(PREFIX + key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

export function writeStorage(key, value) {
  try {
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value))
  } catch {
    /* ignore write failures */
  }
}

export function removeStorage(key) {
  try {
    window.localStorage.removeItem(PREFIX + key)
  } catch {
    /* ignore */
  }
}
