/**
 * components/ProductList.js
 */
import React from "react";
import ProductCard from "./ProductCard";
import CacheBadge from "./CacheBadge";
import "../assets/css/ProductList.css";

export default function ProductList({
  products,
  totalCount,
  loading,
  cacheMeta,
  onCardClick,
  onRefresh,
}) {
  return (
    <section className="product-list">
      <div className="product-list__header">
        <div className="product-list__title">
          <h2>Products</h2>
          {totalCount > 0 && (
            <span className="product-list__count">{totalCount} total</span>
          )}
        </div>
        <div className="product-list__meta">
          <CacheBadge cacheMeta={cacheMeta} />
          <button
            className="btn btn--outline"
            onClick={onRefresh}
            disabled={loading}
          >
            {loading ? "⏳ Loading…" : "🔄 Refresh"}
          </button>
        </div>
      </div>

      {loading && products.length === 0 && (
        <div className="product-list__spinner">
          <div className="spinner" />
          <p>Loading products…</p>
        </div>
      )}

      {!loading && products.length === 0 && (
        <div className="product-list__empty">
          <p>No products found.</p>
          <code>
            docker-compose exec backend python manage.py load_sample_products
          </code>
        </div>
      )}

      <div className="product-grid">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} onClick={onCardClick} />
        ))}
      </div>
    </section>
  );
}
