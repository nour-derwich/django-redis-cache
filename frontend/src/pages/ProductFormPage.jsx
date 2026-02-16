/**
 * pages/ProductFormPage.jsx
 *
 * Route: /products/new          → create mode
 * Route: /products/:id/edit     → edit mode (fetches product by id)
 *
 * Add to App.jsx:
 *   import ProductFormPage from './pages/ProductFormPage.jsx'
 *   <Route path="/products/new"      element={<ProductFormPage />} />
 *   <Route path="/products/:id/edit" element={<ProductFormPage />} />
 */
import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ProductCreateForm from '../components/ProductCreateForm.jsx'
import '../assets/css/ProductFormPage.css'

export default function ProductFormPage() {
  const { id }     = useParams()
  const navigate   = useNavigate()
  const isEditing  = Boolean(id)

  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(isEditing)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    if (!isEditing) return
    import('../services/api.jsx').then(({ productsAPI }) =>
      productsAPI.detail(id)
        .then(r => setProduct(r.data))
        .catch(() => setError('Product not found or failed to load.'))
        .finally(() => setLoading(false))
    )
  }, [id, isEditing])

  function handleSuccess(saved) {
    navigate(`/`, { state: { flash: `"${saved.name}" ${isEditing ? 'updated' : 'created'} successfully!` } })
  }

  if (loading) {
    return (
      <div className="pfp-center">
        <div className="pfp-spinner" />
        <p>Loading product…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="pfp-center">
        <p className="pfp-error">⚠ {error}</p>
        <button className="pfp-back" onClick={() => navigate(-1)}>← Go back</button>
      </div>
    )
  }

  return (
    <div className="pfp-page">
      <div className="pfp-breadcrumb">
        <button onClick={() => navigate('/')} className="pfp-breadcrumb__link">Products</button>
        <span className="pfp-breadcrumb__sep">›</span>
        <span>{isEditing ? 'Edit' : 'New Product'}</span>
      </div>

      <ProductCreateForm
        product={isEditing ? product : undefined}
        onSuccess={handleSuccess}
        onCancel={() => navigate(-1)}
      />
    </div>
  )
}