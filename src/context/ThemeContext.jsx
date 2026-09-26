import { createContext, useContext, useEffect, useState } from 'react'
import { readStorage, writeStorage } from '../utils/storage.js'

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => readStorage('theme', 'light'))

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    writeStorage('theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  return <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
