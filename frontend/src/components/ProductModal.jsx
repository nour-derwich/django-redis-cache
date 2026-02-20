/**
 * components/ProductModal.jsx
 * Detail overlay with edit/delete actions
 */
import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import CacheBadge from './CacheBadge.jsx'
import { useProductDetail } from '../hooks/useProducts.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { productsAPI } from '../services/api.jsx'
import '../assets/css/ProductModal.css'

export default function ProductModal({ productId, onClose, onDelete }) {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const { product, loading, cacheMeta } = useProductDetail(productId)

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  async function handleDelete() {
    if (!window.confirm(`Delete "${product.name}"? This cannot be undone.`)) return
    try {
      await productsAPI.remove(product.id)
      onClose()
      onDelete?.()  // trigger parent refresh
    } catch (err) {
      alert(`Failed to delete: ${err.response?.data?.detail ?? err.message}`)
    }
  }

  function handleEdit() {
    navigate(`/products/${product.id}/edit`)
    onClose()
  }

  if (loading || !product) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal modal--loading">
          <div className="spinner" />
          <p>Loading product...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>

        <div className="modal__header">
          <div>
            <h2 className="modal__title">{product.name}</h2>
            {product.category_name && (
              <span className="modal__category">{product.category_name}</span>
            )}
          </div>
          <div className="modal__header-right">
            <CacheBadge cacheMeta={cacheMeta} />
            <button className="modal__close" onClick={onClose}>✕</button>
          </div>
        </div>

        <div className="modal__body">
          <div className="modal__pricing">
            {product.is_on_sale && (
              <span className="modal__compare">${product.compare_at_price}</span>
            )}
            <span className="modal__price">${product.price}</span>
            {product.is_on_sale && (
              <span className="modal__discount">−{product.discount_percentage}% off</span>
            )}
          </div>

          {product.description && (
            <p className="modal__desc">{product.description}</p>
          )}

          <div className="modal__meta">
            <div className="modal__meta-item">
              <span className="modal__meta-label">SKU</span>
              <span>{product.sku}</span>
            </div>
            <div className="modal__meta-item">
              <span className="modal__meta-label">Stock</span>
              <span>
                {product.stock_quantity} units
                {product.is_low_stock && ' ⚠ Low'}
                {!product.is_in_stock && ' ✗ Out'}
              </span>
            </div>
            <div className="modal__meta-item">
              <span className="modal__meta-label">Status</span>
              <span className={`status status--${product.status}`}>
                {product.status}
              </span>
            </div>
            {product.is_featured && (
              <div className="modal__meta-item">
                <span className="modal__meta-label">Featured</span>
                <span>⭐ Yes</span>
              </div>
            )}
          </div>

          {/* Cache debug table */}
          <div className="modal__cache">
            <div className="modal__cache-title">Cache Debug</div>
            <table>
              <tbody>
                <tr>
                  <td>Cache Hit</td>
                  <td className={cacheMeta.hit ? 'hit' : 'miss'}>
                    {cacheMeta.hit ? '✓ true' : '✗ false'}
                  </td>
                </tr>
                <tr>
                  <td>Response Time</td>
                  <td>{cacheMeta.responseTime ?? 'N/A'} ms</td>
                </tr>
                <tr>
                  <td>Cache Key</td>
                  <td className="monospace">{cacheMeta.key ?? 'N/A'}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Edit/Delete actions (only when authenticated) */}
        {isAuthenticated && (
          <div className="modal__actions">
            <button className="modal__btn modal__btn--delete" onClick={handleDelete}>
              🗑️ Delete Product
            </button>
            <button className="modal__btn modal__btn--edit" onClick={handleEdit}>
              ✏️ Edit Product
            </button>
          </div>
        )}
      </div>
    </div>
  )
}