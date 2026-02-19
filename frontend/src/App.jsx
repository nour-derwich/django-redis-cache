/**
 * App.jsx — Root component with React Router + auth sync
 */
import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import ProductsPage    from './pages/ProductsPage.jsx'
import FeaturedPage    from './pages/FeaturedPage.jsx'
import ProductFormPage from './pages/ProductFormPage.jsx'
import { useAuth }       from './context/AuthContext.jsx'
import LoginPage       from './pages/LoginPage.jsx'
import { setAuthToken } from './services/api.jsx'
import './App.css'

const NAV_LINKS = [
  { to: '/',             label: '📦 Products',    end: true },
  { to: '/featured',     label: '⭐ Featured',     end: true },
  { to: '/products/new', label: '➕ New Product',  end: false },
]

const EXTERNAL = [
  { href: 'http://localhost:8000/api/',   label: 'API'    },
  { href: 'http://localhost:8000/admin/', label: 'Admin'  },
  { href: 'http://localhost:5555',        label: 'Flower' },
]

function Header() {
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <div className="app-header__brand">
          <span className="app-header__logo">🚀</span>
          <div>
            <h1 className="app-header__title">Django Redis Caching Demo</h1>
            <p className="app-header__sub">
              Advanced caching patterns · Django + Redis + Celery + React
            </p>
          </div>
        </div>

        <nav className="app-nav">
          {NAV_LINKS.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `app-nav__link ${isActive ? 'app-nav__link--active' : ''}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="app-auth">
          {isAuthenticated ? (
            <>
              <span className="app-auth__user">👤 {user.username}</span>
              <button className="app-auth__logout" onClick={logout}>Sign out</button>
            </>
          ) : (
            <NavLink to="/login" className="app-auth__signin">Sign in</NavLink>
          )}
        </div>
      </div>
    </header>
  )
}

export default function App() {
  const { token } = useAuth()

  // Keep Axios token in sync with auth state
  useEffect(() => {
    setAuthToken(token)
  }, [token])

  return (
    <BrowserRouter>
      <div className="app">
        <Header />

        <main className="app-main">
          <div className="container">
            <Routes>
              <Route path="/"                element={<ProductsPage />}    />
              <Route path="/featured"        element={<FeaturedPage />}    />
              <Route path="/products/new"    element={<ProductFormPage />} />
              <Route path="/products/:id/edit" element={<ProductFormPage />} />
              <Route path="/login" element={<LoginPage />} />
            </Routes>
          </div>
        </main>

        <footer className="app-footer">
          <p>Built for learning Redis caching patterns</p>
          <div className="app-footer__links">
            {EXTERNAL.map(({ href, label }) => (
              <a key={href} href={href} target="_blank" rel="noreferrer">{label}</a>
            ))}
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}