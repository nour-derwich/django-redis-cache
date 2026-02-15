/**
 * pages/FeaturedPage.js
 * Shows only featured products — cached separately under "products_featured".
 */
import React from "react";
import ProductCard from "../components/ProductCard";
import CacheBadge from "../components/CacheBadge";
import { useFeaturedProducts } from "../hooks/useProducts";
import "./FeaturedPage.css";

export default function FeaturedPage() {
  const { products, loading, cacheMeta } = useFeaturedProducts();

  return (
    <div className="featured-page">
      <div className="featured-page__header">
        <div>
          <h2>⭐ Featured Products</h2>
          <p className="featured-page__sub">
            Cached separately under <code>products_featured</code> key (5 min
            TTL)
          </p>
        </div>
        <CacheBadge cacheMeta={cacheMeta} />
      </div>

      {loading && (
        <div className="featured-page__loading">
          <div className="spinner" />
          <p>Loading featured products…</p>
        </div>
      )}

      {!loading && products.length === 0 && (
        <div className="featured-page__empty">
          <p>No featured products yet.</p>
          <small>
            Mark products as featured in the{" "}
            <a
              href="http://localhost:8000/admin/"
              target="_blank"
              rel="noreferrer"
            >
              Django Admin
            </a>
          </small>
        </div>
      )}

      <div className="product-grid">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  );
}
