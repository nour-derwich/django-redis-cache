/**
 * components/ProductCard.jsx
 */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import '../assets/css/ProductCard.css'

export default function ProductCard({ product, onClick, onDelete }) {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const {
    id, name, price, compare_at_price, is_on_sale, discount_percentage,
    stock_quantity, is_in_stock, is_low_stock,
    category_name, short_description, is_featured, status,
  } = product

  function handleEdit(e) {
    e.stopPropagation()
    navigate(`/products/${id}/edit`)
  }

  function handleDelete(e) {
    e.stopPropagation()
    if (window.confirm(`Delete "${name}"? This cannot be undone.`)) {
      onDelete?.(product)
    }
  }

  return (
    <div
      className={`product-card ${!is_in_stock ? 'oos' : ''}`}
      onClick={() => onClick?.(product)}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {is_featured && <span className="badge badge--featured">⭐ Featured</span>}
      {is_on_sale   && <span className="badge badge--sale">−{discount_percentage}%</span>}

      {/* Edit/Delete actions — only show when authenticated */}
      {isAuthenticated && (
        <div className="product-card__actions">
          <button
            className="product-card__action product-card__action--edit"
            onClick={handleEdit}
            title="Edit product"
            aria-label="Edit product"
          >
            ✏️
          </button>
          <button
            className="product-card__action product-card__action--delete"
            onClick={handleDelete}
            title="Delete product"
            aria-label="Delete product"
          >
            🗑️
          </button>
        </div>
      )}

      <div className="product-card__img">📦</div>

      <div className="product-card__body">
        {category_name && (
          <span className="product-card__category">{category_name}</span>
        )}
        <h3 className="product-card__name">{name}</h3>
        {short_description && (
          <p className="product-card__desc">{short_description}</p>
        )}

        <div className="product-card__pricing">
          {is_on_sale && (
            <span className="product-card__compare">${compare_at_price}</span>
          )}
          <span className="product-card__price">${price}</span>
        </div>

        <div className="product-card__stock">
          {!is_in_stock   && <span className="stock stock--out">✗ Out of stock</span>}
          {is_low_stock   && <span className="stock stock--low">⚠ Low stock ({stock_quantity})</span>}
          {is_in_stock && !is_low_stock && (
            <span className="stock stock--ok">✓ In stock ({stock_quantity})</span>
          )}
        </div>

        {status === 'draft' && (
          <span className="product-card__status">Draft</span>
        )}
      </div>
    </div>
  )
}