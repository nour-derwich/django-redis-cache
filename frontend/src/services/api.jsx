/**
 * services/api.jsx
 *
 * Central Axios instance.
 * Call setAuthToken(token) after login — the interceptor attaches it to
 * every request automatically. Call setAuthToken(null) on logout.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Auth token injection ──────────────────────────────────────────────────
let _token = null
export function setAuthToken(token) {
  _token = token
}

api.interceptors.request.use(config => {
  if (_token) {
    config.headers.Authorization = `Bearer ${_token}`
  }
  return config
})

// ── Cache meta from response headers ─────────────────────────────────────
api.interceptors.response.use(
  response => {
    response.cacheMeta = {
      hit:          response.headers['x-cache-hit'] === 'true',
      responseTime: response.headers['x-cache-response-time'] ?? null,
      key:          response.headers['x-cache-key'] ?? null,
    }
    return response
  },
  error => Promise.reject(error)
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