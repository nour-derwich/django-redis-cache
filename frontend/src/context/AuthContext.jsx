/**
 * context/AuthContext.jsx
 * Global auth state with JWT. Tokens stored in memory only.
 */
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import axios from 'axios'

// Same base as Vite proxy → /api routes to backend:8000
const AUTH_BASE = '/api'

const AuthContext = createContext(null)

function decodeToken(jwt) {
  try {
    return JSON.parse(atob(jwt.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token,   setToken]   = useState(null)
  const [refresh, setRefresh] = useState(null)
  const [user,    setUser]    = useState(null)
  const [loading, setLoading] = useState(false)

  const login = useCallback(async (username, password) => {
    setLoading(true)
    try {
      const res = await axios.post(
        `${AUTH_BASE}/auth/login/`,
        { username, password },
        { headers: { 'Content-Type': 'application/json' } }
      )
      const { access, refresh: ref } = res.data
      const payload = decodeToken(access)
      setToken(access)
      setRefresh(ref)
      setUser({
        username: payload?.username ?? username,
        is_staff: payload?.is_staff ?? false,
        user_id:  payload?.user_id,
      })
      return { ok: true }
    } catch (err) {
      const data = err.response?.data
      const msg  = data?.detail ?? data?.non_field_errors?.[0]
               ?? err.message ?? 'Login failed'
      return { ok: false, error: msg }
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setRefresh(null)
    setUser(null)
  }, [])

  // Auto-refresh 1 min before expiry
  useEffect(() => {
    if (!token || !refresh) return
    const payload = decodeToken(token)
    if (!payload?.exp) return
    const ms = payload.exp * 1000 - Date.now() - 60_000
    if (ms <= 0) return
    const tid = setTimeout(async () => {
      try {
        const res = await axios.post(
          `${AUTH_BASE}/auth/refresh/`,
          { refresh },
          { headers: { 'Content-Type': 'application/json' } }
        )
        setToken(res.data.access)
      } catch {
        logout()
      }
    }, ms)
    return () => clearTimeout(tid)
  }, [token, refresh, logout])

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: Boolean(token), login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside <AuthProvider>')
  return ctx
}