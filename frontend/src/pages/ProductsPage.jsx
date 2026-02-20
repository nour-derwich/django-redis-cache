/**
 * pages/ProductsPage.jsx
 */
import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import ProductList from '../components/ProductList.jsx'
import FilterBar from '../components/FilterBar.jsx'
import ProductModal from '../components/ProductModal.jsx'
import CacheStats from '../components/CacheStats.jsx'
import { useProducts } from '../hooks/useProducts.jsx'
import { useCategories } from '../hooks/useCategories.jsx'
import { productsAPI } from '../services/api.jsx'
import '../assets/css/ProductsPage.css'

export default function ProductsPage() {
  const location = useLocation()
  const navigate = useNavigate()

  const [filters, setFilters] = useState({})
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [toast, setToast] = useState(null)

  const { products, totalCount, loading, error, cacheMeta, refetch } = useProducts(filters)
  const { categories } = useCategories()

  // Listen for navigation state (after create/edit)
  useEffect(() => {
    if (location.state?.toast) {
      showToast(location.state.toast.message, location.state.toast.type)
    }
    if (location.state?.refetch) {
      // Wait 300ms for backend cache invalidation to propagate
      setTimeout(() => refetch(), 300)
    }
    // Clear state after consuming it
    if (location.state) {
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location.state])

  function showToast(message, type = 'info') {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3500)
  }

  async function handleDelete(product) {
    try {
      await productsAPI.remove(product.id)
      showToast(`"${product.name}" deleted`, 'success')
      setTimeout(() => refetch(), 300)
    } catch (err) {
      showToast(`Delete failed: ${err.response?.data?.detail ?? err.message}`, 'error')
    }
  }

  function handleModalClose() {
    setSelectedProduct(null)
  }

  return (
    <div className="products-page">
      <CacheStats />

      <FilterBar
        filters={filters}
        onFilterChange={setFilters}
        categories={categories}
      />

      {/* Toast notification */}
      {toast && (
        <div className={`toast toast--${toast.type}`}>
          <span className="toast__icon">
            {toast.type === 'success' && '✓'}
            {toast.type === 'error' && '✗'}
            {toast.type === 'info' && 'ℹ'}
          </span>
          {toast.message}
        </div>
      )}

      <ProductList
        products={products}
        totalCount={totalCount}
        loading={loading}
        error={error}
        cacheMeta={cacheMeta}
        onRefresh={refetch}
        onCardClick={setSelectedProduct}
        onDelete={handleDelete}
      />

      {selectedProduct && (
        <ProductModal
          productId={selectedProduct.id}
          onClose={handleModalClose}
          onDelete={() => {
            handleModalClose()
            showToast('Product deleted', 'success')
            setTimeout(() => refetch(), 300)
          }}
        />
      )}
    </div>
  )
}