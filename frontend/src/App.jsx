/**
 * App.js
 * Root component with React Router navigation between pages.
 */
import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import ProductsPage from './pages/ProductsPage';
import FeaturedPage from './pages/FeaturedPage';
import './App.css';

const LINKS = [
  { to: '/',         label: '📦 Products'  },
  { to: '/featured', label: '⭐ Featured'  },
];

const EXTERNAL = [
  { href: 'http://localhost:8000/api/',    label: 'API' },
  { href: 'http://localhost:8000/admin/',  label: 'Admin' },
  { href: 'http://localhost:5555',         label: 'Flower' },
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">

        {/* ── Header ── */}
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
              {LINKS.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end
                  className={({ isActive }) =>
                    `app-nav__link ${isActive ? 'app-nav__link--active' : ''}`
                  }
                >
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>
        </header>

        {/* ── Main ── */}
        <main className="app-main">
          <div className="container">
            <Routes>
              <Route path="/"         element={<ProductsPage />} />
              <Route path="/featured" element={<FeaturedPage />} />
            </Routes>
          </div>
        </main>

        {/* ── Footer ── */}
        <footer className="app-footer">
          <p>Built for learning Redis caching patterns</p>
          <div className="app-footer__links">
            {EXTERNAL.map(({ href, label }) => (
              <a key={href} href={href} target="_blank" rel="noreferrer">
                {label}
              </a>
            ))}
          </div>
        </footer>

      </div>
    </BrowserRouter>
  );
}