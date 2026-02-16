/**
 * pages/ProductsPage.js
 * Main product listing page with filter bar, product grid, and cache indicators.
 */
import React, { useState } from "react";
import ProductList from "../components/ProductList";
import CacheStats from "../components/CacheStats";
import ProductModal from "../components/ProductModal";
import FilterBar from "../components/FilterBar";
import { useProducts } from "../hooks/useProducts";
import { useCategories } from "../hooks/useCategories";
import "../assets/css/ProductsPage.css";

export default function ProductsPage() {
  const [filters, setFilters] = useState({});
  const [selectedProduct, setSelectedProduct] = useState(null);

  const { categories } = useCategories();
  const { products, totalCount, loading, error, cacheMeta, refetch } =
    useProducts(filters);

  return (
    <div className="products-page">
      <CacheStats />

      <FilterBar
        categories={categories}
        filters={filters}
        onChange={setFilters}
      />

      {error && (
        <div className="alert alert--error">
          ⚠ Could not reach the API: <strong>{error}</strong>
          <br />
          <small>
            Make sure Django is running: <code>docker-compose up -d</code>
          </small>
        </div>
      )}

      <ProductList
        products={products}
        totalCount={totalCount}
        loading={loading}
        cacheMeta={cacheMeta}
        onCardClick={setSelectedProduct}
        onRefresh={refetch}
      />

      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
        />
      )}
    </div>
  );
}
