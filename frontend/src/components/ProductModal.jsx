/**
 * components/ProductModal.js
 * Detail overlay shown when a product card is clicked.
 * Fetches from /api/products/:id/ so you can see the cache hit header live.
 */
import React, { useEffect } from "react";
import CacheBadge from "./CacheBadge";
import { useProductDetail } from "../hooks/useProducts";
import "../assets/css/ProductModal.css";

export default function ProductModal({ product: summary, onClose }) {
  const { product, loading, cacheMeta } = useProductDetail(summary.id);
  const p = product || summary;

  /* close on Escape key */
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <div>
            <h2 className="modal__title">{p.name}</h2>
            {p.category_name && (
              <span className="modal__category">{p.category_name}</span>
            )}
          </div>
          <div className="modal__header-right">
            {loading ? (
              <span className="modal__loading">Fetching…</span>
            ) : (
              <CacheBadge cacheMeta={cacheMeta} />
            )}
            <button className="modal__close" onClick={onClose}>
              ✕
            </button>
          </div>
        </div>

        <div className="modal__body">
          <div className="modal__pricing">
            {p.is_on_sale && (
              <span className="modal__compare">${p.compare_at_price}</span>
            )}
            <span className="modal__price">${p.price}</span>
            {p.is_on_sale && (
              <span className="modal__discount">
                −{p.discount_percentage}% off
              </span>
            )}
          </div>

          {p.description && <p className="modal__desc">{p.description}</p>}

          <div className="modal__meta">
            <div className="modal__meta-item">
              <span className="modal__meta-label">SKU</span>
              <span>{p.sku}</span>
            </div>
            <div className="modal__meta-item">
              <span className="modal__meta-label">Stock</span>
              <span
                className={
                  !p.is_in_stock
                    ? "stock--out"
                    : p.is_low_stock
                      ? "stock--low"
                      : "stock--ok"
                }
              >
                {p.stock_quantity} units
              </span>
            </div>
            <div className="modal__meta-item">
              <span className="modal__meta-label">Status</span>
              <span>{p.status}</span>
            </div>
            {p.is_featured && (
              <div className="modal__meta-item">
                <span className="modal__meta-label">⭐ Featured</span>
                <span>Yes</span>
              </div>
            )}
          </div>

          {cacheMeta && (
            <div className="modal__cache-detail">
              <h4>🔍 Cache Debug</h4>
              <table>
                <tbody>
                  <tr>
                    <td>Cache hit</td>
                    <td>{cacheMeta.hit ? "✅ Yes" : "❌ No (DB hit)"}</td>
                  </tr>
                  <tr>
                    <td>Response time</td>
                    <td>{cacheMeta.responseTime ?? "—"} ms</td>
                  </tr>
                  <tr>
                    <td>Cache key</td>
                    <td>
                      <code>{cacheMeta.key ?? `product_${p.id}`}</code>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
