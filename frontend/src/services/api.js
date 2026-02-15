/**
 * services/api.js
 * Central Axios instance + every API call used by the app.
 * Reads X-Cache-Hit and X-Cache-Response-Time headers from the
 * Django CacheMonitorMiddleware and attaches them to every response.
 */
import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

// ── Axios instance ───────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// ── Response interceptor — attach cache meta ─────────────────────────────────

api.interceptors.response.use(
  (response) => {
    response.cacheMeta = {
      hit: response.headers["x-cache-hit"] === "true",
      responseTime: response.headers["x-cache-response-time"] ?? null,
      key: response.headers["x-cache-key"] ?? null,
    };
    return response;
  },
  (error) => Promise.reject(error),
);

// ── Products ─────────────────────────────────────────────────────────────────

export const productsAPI = {
  /** GET /products/  — accepts { status, category, is_featured, page } */
  list: (params = {}) => api.get("/products/", { params }),

  /** GET /products/:id/ */
  detail: (id) => api.get(`/products/${id}/`),

  /** POST /products/ */
  create: (data) => api.post("/products/", data),

  /** PATCH /products/:id/ */
  update: (id, data) => api.patch(`/products/${id}/`, data),

  /** DELETE /products/:id/ */
  remove: (id) => api.delete(`/products/${id}/`),

  /** GET /products/featured/ */
  featured: () => api.get("/products/featured/"),

  /** GET /products/statistics/ */
  statistics: () => api.get("/products/statistics/"),

  /** POST /products/clear_cache/  — staff only */
  clearCache: () => api.post("/products/clear_cache/"),
};

// ── Categories ───────────────────────────────────────────────────────────────

export const categoriesAPI = {
  /** GET /categories/ */
  list: () => api.get("/categories/"),

  /** GET /categories/:slug/ */
  detail: (slug) => api.get(`/categories/${slug}/`),

  /** GET /categories/:slug/products/ */
  products: (slug) => api.get(`/categories/${slug}/products/`),
};

export default api;
