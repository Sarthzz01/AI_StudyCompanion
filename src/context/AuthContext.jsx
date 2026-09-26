import { createContext, useContext, useEffect, useState } from 'react'
import { loginUser, signupUser, logoutUser, getCurrentUser } from '../services/api.js'
import { readStorage, writeStorage, removeStorage } from '../utils/storage.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => readStorage('user', null))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    const token = readStorage('token', null)
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }

    // Verify token with backend /auth/me
    getCurrentUser()
      .then((currentUser) => {
        if (mounted) {
          setUser(currentUser)
          writeStorage('user', currentUser)
        }
      })
      .catch(() => {
        if (mounted) {
          setUser(null)
          removeStorage('token')
          removeStorage('user')
        }
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [])

  const login = async (credentials) => {
    const profile = await loginUser(credentials)
    setUser(profile)
    writeStorage('user', profile)
    return profile
  }

  const signup = async (details) => {
    const profile = await signupUser(details)
    setUser(profile)
    writeStorage('user', profile)
    return profile
  }

  const logout = async () => {
    await logoutUser()
    setUser(null)
    removeStorage('token')
    removeStorage('user')
  }

  const updateUser = (changes) => {
    setUser((current) => {
      const next = { ...current, ...changes }
      writeStorage('user', next)
      return next
    })
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: Boolean(user),
        login,
        signup,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
