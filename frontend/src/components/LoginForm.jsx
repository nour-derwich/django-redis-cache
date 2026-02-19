/**
 * components/LoginForm.jsx
 *
 * Shown when user tries to access a protected action (create/edit).
 * Calls useAuth().login() and resolves a promise on success.
 */
import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import './LoginForm.css'

export default function LoginForm({ onSuccess, onCancel, message }) {
  const { login, loading } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    const result = await login(username, password)
    if (result.ok) {
      onSuccess?.()
    } else {
      setError(result.error)
    }
  }

  return (
    <div className="lf-overlay" onClick={e => { if (e.target === e.currentTarget) onCancel?.() }}>
      <div className="lf-card">

        <div className="lf-header">
          <div className="lf-icon">🔐</div>
          <h2 className="lf-title">Sign in required</h2>
          {message && <p className="lf-message">{message}</p>}
        </div>

        {error && (
          <div className="lf-error" role="alert">
            ⚠ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="lf-form">
          <div className="lf-field">
            <label className="lf-label">Username</label>
            <input
              className="lf-input"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoFocus
              autoComplete="username"
              required
            />
          </div>

          <div className="lf-field">
            <label className="lf-label">Password</label>
            <input
              className="lf-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          <button type="submit" className="lf-btn" disabled={loading}>
            {loading
              ? <><span className="lf-spinner" /> Signing in…</>
              : 'Sign in'}
          </button>
        </form>

        <p className="lf-hint">
          Use your Django admin credentials.{' '}
          <a href="http://localhost:8000/admin/" target="_blank" rel="noreferrer">
            Create a user →
          </a>
        </p>

        {onCancel && (
          <button className="lf-cancel" onClick={onCancel}>Cancel</button>
        )}
      </div>
    </div>
  )
}