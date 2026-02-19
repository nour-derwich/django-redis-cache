/**
 * pages/LoginPage.jsx
 * Route: /login
 *
 * Dedicated login page — always accessible from nav.
 * Redirects to /  (or ?next= param) after successful login.
 */
import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import '../assets/css/LoginPage.css'

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const navigate      = useNavigate()
  const [params]      = useSearchParams()
  const next          = params.get('next') || '/'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState(null)
  const [lines,    setLines]    = useState([])  // terminal animation lines

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) navigate(next, { replace: true })
  }, [isAuthenticated, navigate, next])

  // Boot-up terminal animation
  useEffect(() => {
    const sequence = [
      { text: '$ connecting to redis_demo_backend...', delay: 0 },
      { text: '> host: backend:8000  ✓', delay: 400 },
      { text: '> redis: redis:6379   ✓', delay: 750 },
      { text: '> jwt: simplejwt      ✓', delay: 1050 },
      { text: '$ awaiting credentials_', delay: 1350 },
    ]
    const timers = sequence.map(({ text, delay }) =>
      setTimeout(() => setLines(l => [...l, text]), delay)
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLines(l => [...l, `$ POST /api/auth/login/ → authenticating...`])
    const result = await login(username, password)
    if (result.ok) {
      setLines(l => [...l, '> 200 OK  access_token obtained ✓', '$ redirecting...'])
    } else {
      setLines(l => [...l, `> 401  ${result.error}`])
      setError(result.error)
    }
  }

  return (
    <div className="lp-root">
      {/* Background grid */}
      <div className="lp-grid" aria-hidden />

      <div className="lp-layout">

        {/* Terminal panel */}
        <div className="lp-terminal">
          <div className="lp-terminal__bar">
            <span className="lp-dot lp-dot--red" />
            <span className="lp-dot lp-dot--yellow" />
            <span className="lp-dot lp-dot--green" />
            <span className="lp-terminal__title">redis_demo — bash</span>
          </div>
          <div className="lp-terminal__body">
            {lines.map((line, i) => (
              <div key={i} className={`lp-line ${line.startsWith('>') ? 'lp-line--out' : ''} ${line.includes('✓') ? 'lp-line--ok' : ''} ${line.includes('401') ? 'lp-line--err' : ''}`}>
                {line}
              </div>
            ))}
            <div className="lp-cursor" />
          </div>
        </div>

        {/* Login card */}
        <div className="lp-card">
          <div className="lp-card__header">
            <div className="lp-badge">JWT</div>
            <h1 className="lp-title">Sign in</h1>
            <p className="lp-sub">Use your Django superuser credentials</p>
          </div>

          {error && (
            <div className="lp-alert" role="alert">
              <span className="lp-alert__icon">✗</span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="lp-form">
            <div className="lp-field">
              <label className="lp-label" htmlFor="lp-username">Username</label>
              <input
                id="lp-username"
                className="lp-input"
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoFocus
                autoComplete="username"
                spellCheck={false}
                required
              />
            </div>

            <div className="lp-field">
              <label className="lp-label" htmlFor="lp-password">Password</label>
              <input
                id="lp-password"
                className="lp-input"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>

            <button type="submit" className="lp-btn" disabled={loading}>
              {loading
                ? <><span className="lp-spinner" /> Authenticating…</>
                : '→ Sign in'}
            </button>
          </form>

          <div className="lp-footer">
            <p>No account?</p>
            <a
              href="http://localhost:8000/admin/auth/user/add/"
              target="_blank"
              rel="noreferrer"
              className="lp-link"
            >
              Create one in Django admin ↗
            </a>
            <p className="lp-footer__cmd">
              or: <code>docker exec -it redis_demo_backend python manage.py createsuperuser</code>
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}