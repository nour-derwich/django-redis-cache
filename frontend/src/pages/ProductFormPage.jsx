/**
 * pages/ProductFormPage.jsx
 *
 * Route: /products/new          → create mode
 * Route: /products/:id/edit     → edit mode (fetches product by id)
 */
import React, { useEffect, useState } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import ProductCreateForm from '../components/ProductCreateForm.jsx'
import LoginForm         from '../components/LoginForm.jsx'
import { useAuth }       from '../context/AuthContext.jsx'
import { productsAPI }   from '../services/api.jsx'
import '../assets/css/ProductFormPage.css'

export default function ProductFormPage() {
  const { id }              = useParams()
  const navigate            = useNavigate()
  const location            = useLocation()
  const { isAuthenticated } = useAuth()
  const isEditing           = Boolean(id)

  const [product,   setProduct]   = useState(null)
  const [loading,   setLoading]   = useState(isEditing)
  const [error,     setError]     = useState(null)
  const [showLogin, setShowLogin] = useState(false)

  // Show login modal if not authenticated
  useEffect(() => {
    if (!isAuthenticated) setShowLogin(true)
    else setShowLogin(false)
  }, [isAuthenticated])

  // Fetch product when editing
  useEffect(() => {
    if (!isEditing || !isAuthenticated) return
    setLoading(true)
    productsAPI.detail(id)
      .then(r => setProduct(r.data))
      .catch(() => setError('Product not found or failed to load.'))
      .finally(() => setLoading(false))
  }, [id, isEditing, isAuthenticated])

  function handleSuccess(saved) {
    const action = isEditing ? 'updated' : 'created'
    // Navigate back with state that triggers parent refetch
    navigate('/', {
      replace: true,
      state: {
        toast: {
          message: `"${saved.name}" ${action} successfully`,
          type: 'success',
        },
        refetch: true,  // signal to ProductsPage to refetch
      },
    })
  }

  if (showLogin) {
    return (
      <LoginForm
        message="You need to sign in to create or edit products."
        onSuccess={() => setShowLogin(false)}
        onCancel={() => navigate(-1)}
      />
    )
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