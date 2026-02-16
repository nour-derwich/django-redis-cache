/**
 * services/api.jsx
 * Central Axios instance + every API call used by the app.
 *
 * In development: Vite proxies /api → http://backend:8000
 *   so BASE_URL is just '/api' (no hostname needed, no CORS issues).
 * In production: set VITE_API_URL env var at build time.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

// ── Axios instance ────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

// ── Response interceptor — attach cache meta ──────────────────────────────

api.interceptors.response.use(
  (response) => {
    response.cacheMeta = {
      hit:          response.headers['x-cache-hit'] === 'true',
      responseTime: response.headers['x-cache-response-time'] ?? null,
      key:          response.headers['x-cache-key'] ?? null,
    }
    return response
  },
  (error) => Promise.reject(error)
)

// ── Products ──────────────────────────────────────────────────────────────

export const productsAPI = {
  list:       (params = {}) => api.get('/products/', { params }),
  detail:     (id)          => api.get(`/products/${id}/`),
  create:     (data)        => api.post('/products/', data),
  update:     (id, data)    => api.patch(`/products/${id}/`, data),
  remove:     (id)          => api.delete(`/products/${id}/`),
  featured:   ()            => api.get('/products/featured/'),
  statistics: ()            => api.get('/products/statistics/'),
  clearCache: ()            => api.post('/products/clear_cache/'),
}

// ── Categories ────────────────────────────────────────────────────────────

export const categoriesAPI = {
  list:     ()     => api.get('/categories/'),
  detail:   (slug) => api.get(`/categories/${slug}/`),
  products: (slug) => api.get(`/categories/${slug}/products/`),
}

export default api
