/**
 * components/ProductCreateForm.jsx
 *
 * Full create/edit form for products.
 * - POST to /api/products/        when creating
 * - PATCH to /api/products/:id/   when editing (pass `product` prop)
 */
import React, { useState, useEffect } from 'react'
import { productsAPI } from '../services/api.jsx'
import { useCategories } from '../hooks/useCategories.jsx'
import '../assets/css/ProductCreateForm.css'

// ── helpers ──────────────────────────────────────────────────────────────────

const EMPTY = {
  name: '',
  slug: '',
  sku: '',
  short_description: '',
  description: '',
  category: '',
  price: '',
  compare_at_price: '',
  cost: '',
  stock_quantity: '',
  low_stock_threshold: '10',
  status: 'draft',
  is_featured: false,
  meta_title: '',
  meta_description: '',
}

function slugify(str) {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function toFormState(product) {
  if (!product) return EMPTY
  
  // Extract category ID — API returns full object {id, name, slug, ...}
  const categoryId = product.category?.id ?? product.category ?? ''
  
  return {
    name:               product.name               ?? '',
    slug:               product.slug               ?? '',
    sku:                product.sku                ?? '',
    short_description:  product.short_description  ?? '',
    description:        product.description        ?? '',
    category:           categoryId,  // ← use category.id, not the whole object
    price:              product.price              ?? '',
    compare_at_price:   product.compare_at_price   ?? '',
    cost:               product.cost               ?? '',
    stock_quantity:     product.stock_quantity      ?? '',
    low_stock_threshold:product.low_stock_threshold ?? '10',
    status:             product.status             ?? 'draft',
    is_featured:        product.is_featured        ?? false,
    meta_title:         product.meta_title         ?? '',
    meta_description:   product.meta_description   ?? '',
  }
}

// ── sub-components ───────────────────────────────────────────────────────────

function Field({ label, error, required, hint, children }) {
  return (
    <div className={`pcf-field ${error ? 'pcf-field--error' : ''}`}>
      <label className="pcf-label">
        {label}
        {required && <span className="pcf-required" aria-hidden>*</span>}
      </label>
      {children}
      {hint && !error && <p className="pcf-hint">{hint}</p>}
      {error && <p className="pcf-error-msg" role="alert">{error}</p>}
    </div>
  )
}

function Input({ name, value, onChange, type = 'text', placeholder, min, step, ...rest }) {
  return (
    <input
      className="pcf-input"
      type={type}
      name={name}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      min={min}
      step={step}
      {...rest}
    />
  )
}

function Section({ title, children }) {
  return (
    <fieldset className="pcf-section">
      <legend className="pcf-section__title">{title}</legend>
      <div className="pcf-section__body">{children}</div>
    </fieldset>
  )
}

// ── main component ────────────────────────────────────────────────────────────

export default function ProductCreateForm({ product: initialProduct, onSuccess, onCancel }) {
  const isEditing = Boolean(initialProduct?.id)
  const { categories } = useCategories()

  const [form,        setForm]        = useState(() => toFormState(initialProduct))
  const [errors,      setErrors]      = useState({})
  const [submitting,  setSubmitting]  = useState(false)
  const [serverError, setServerError] = useState(null)
  const [slugEdited,  setSlugEdited]  = useState(isEditing)

  // Auto-generate slug from name (only when creating and user hasn't touched slug)
  useEffect(() => {
    if (!slugEdited && form.name) {
      setForm(f => ({ ...f, slug: slugify(f.name) }))
    }
  }, [form.name, slugEdited])

  // ── handlers ────────────────────────────────────────────────────────────

  function handleChange(e) {
    const { name, value, type, checked } = e.target
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
    if (errors[name]) setErrors(e => { const n = { ...e }; delete n[name]; return n })
    if (name === 'slug') setSlugEdited(true)
  }

  function validate() {
    const e = {}
    if (!form.name.trim())            e.name  = 'Name is required'
    if (!form.sku.trim())             e.sku   = 'SKU is required'
    if (!form.slug.trim())            e.slug  = 'Slug is required'
    if (!form.price)                  e.price = 'Price is required'
    if (isNaN(Number(form.price)) || Number(form.price) < 0)
                                      e.price = 'Price must be a positive number'
    if (form.compare_at_price && Number(form.compare_at_price) <= Number(form.price))
      e.compare_at_price = 'Compare-at price must be higher than the sale price'
    if (form.stock_quantity === '')   e.stock_quantity = 'Stock quantity is required'
    if (Number(form.stock_quantity) < 0)
      e.stock_quantity = 'Stock cannot be negative'
    return e
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const validationErrors = validate()
    if (Object.keys(validationErrors).length) {
      setErrors(validationErrors)
      document.querySelector('.pcf-field--error')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      return
    }

    setSubmitting(true)
    setServerError(null)

    // Build payload — omit empty optional fields
    const payload = { ...form }
    if (!payload.compare_at_price) delete payload.compare_at_price
    if (!payload.cost)             delete payload.cost
    if (!payload.category)         delete payload.category
    if (!payload.meta_title)       delete payload.meta_title
    if (!payload.meta_description) delete payload.meta_description

    try {
      const res = isEditing
        ? await productsAPI.update(initialProduct.id, payload)
        : await productsAPI.create(payload)
      onSuccess?.(res.data)
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        const fieldErrors = {}
        let generic = null
        for (const [key, val] of Object.entries(data)) {
          const msg = Array.isArray(val) ? val.join(' ') : String(val)
          if (key in EMPTY) {
            fieldErrors[key] = msg
          } else {
            generic = (generic ? generic + ' ' : '') + msg
          }
        }
        if (Object.keys(fieldErrors).length) setErrors(fieldErrors)
        if (generic) setServerError(generic)
      } else {
        setServerError(err.message || 'Something went wrong. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  // ── render ───────────────────────────────────────────────────────────────

  return (
    <div className="pcf-wrapper">
      <div className="pcf-header">
        <div className="pcf-header__icon">{isEditing ? '✏️' : '📦'}</div>
        <div>
          <h2 className="pcf-header__title">
            {isEditing ? `Edit — ${initialProduct.name}` : 'Create Product'}
          </h2>
          <p className="pcf-header__sub">
            {isEditing
              ? 'Changes will invalidate the Redis cache automatically via signals.'
              : 'New product will be saved to DB and a cache key will be created on first fetch.'}
          </p>
        </div>
      </div>

      {serverError && (
        <div className="pcf-server-error" role="alert">
          <span>⚠ {serverError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>

        {/* ── Basic info ──────────────────────────────────────────── */}
        <Section title="Basic Information">
          <div className="pcf-row">
            <Field label="Product Name" error={errors.name} required>
              <Input
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="e.g. Wireless Noise-Cancelling Headphones"
                autoFocus
              />
            </Field>
            <Field label="SKU" error={errors.sku} required hint="Unique identifier used in inventory systems">
              <Input
                name="sku"
                value={form.sku}
                onChange={handleChange}
                placeholder="e.g. WH-1000XM5"
              />
            </Field>
          </div>

          <div className="pcf-row">
            <Field label="Slug" error={errors.slug} required hint="Auto-generated from name — used in URLs">
              <div className="pcf-input-prefix">
                <span className="pcf-prefix">/products/</span>
                <Input
                  name="slug"
                  value={form.slug}
                  onChange={handleChange}
                  placeholder="wireless-headphones"
                />
              </div>
            </Field>
            <Field label="Category" error={errors.category}>
              <select
                className="pcf-input pcf-select"
                name="category"
                value={form.category}
                onChange={handleChange}
              >
                <option value="">— No category —</option>
                {categories.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="Short Description" error={errors.short_description} hint="Shown on product cards (max ~150 chars)">
            <Input
              name="short_description"
              value={form.short_description}
              onChange={handleChange}
              placeholder="One compelling sentence about the product"
              maxLength={160}
            />
          </Field>

          <Field label="Description" error={errors.description}>
            <textarea
              className="pcf-input pcf-textarea"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Full product description..."
              rows={5}
            />
          </Field>
        </Section>

        {/* ── Pricing ─────────────────────────────────────────────── */}
        <Section title="Pricing">
          <div className="pcf-row pcf-row--3">
            <Field label="Price" error={errors.price} required>
              <div className="pcf-input-prefix">
                <span className="pcf-prefix">$</span>
                <Input
                  name="price"
                  value={form.price}
                  onChange={handleChange}
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                />
              </div>
            </Field>
            <Field label="Compare-at Price" error={errors.compare_at_price} hint="Original price before sale">
              <div className="pcf-input-prefix">
                <span className="pcf-prefix">$</span>
                <Input
                  name="compare_at_price"
                  value={form.compare_at_price}
                  onChange={handleChange}
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                />
              </div>
            </Field>
            <Field label="Cost" error={errors.cost} hint="Your cost (not shown to customers)">
              <div className="pcf-input-prefix">
                <span className="pcf-prefix">$</span>
                <Input
                  name="cost"
                  value={form.cost}
                  onChange={handleChange}
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                />
              </div>
            </Field>
          </div>

          {form.compare_at_price && form.price && Number(form.compare_at_price) > Number(form.price) && (
            <div className="pcf-discount-preview">
              <span>🏷 Sale: </span>
              <strong>
                {Math.round((1 - Number(form.price) / Number(form.compare_at_price)) * 100)}% off
              </strong>
              <span> — saving ${(Number(form.compare_at_price) - Number(form.price)).toFixed(2)}</span>
            </div>
          )}
        </Section>

        {/* ── Inventory ────────────────────────────────────────────── */}
        <Section title="Inventory">
          <div className="pcf-row">
            <Field label="Stock Quantity" error={errors.stock_quantity} required>
              <Input
                name="stock_quantity"
                value={form.stock_quantity}
                onChange={handleChange}
                type="number"
                min="0"
                step="1"
                placeholder="0"
              />
            </Field>
            <Field label="Low Stock Threshold" error={errors.low_stock_threshold} hint="Alert when stock falls below this">
              <Input
                name="low_stock_threshold"
                value={form.low_stock_threshold}
                onChange={handleChange}
                type="number"
                min="0"
                step="1"
                placeholder="10"
              />
            </Field>
          </div>
        </Section>

        {/* ── Status ───────────────────────────────────────────────── */}
        <Section title="Status &amp; Visibility">
          <div className="pcf-row">
            <Field label="Status" error={errors.status}>
              <select
                className="pcf-input pcf-select"
                name="status"
                value={form.status}
                onChange={handleChange}
              >
                <option value="draft">Draft — hidden from public</option>
                <option value="published">Published — visible to everyone</option>
                <option value="archived">Archived — discontinued</option>
              </select>
            </Field>

            <Field label="Featured">
              <label className="pcf-toggle">
                <input
                  type="checkbox"
                  name="is_featured"
                  checked={form.is_featured}
                  onChange={handleChange}
                />
                <span className="pcf-toggle__track">
                  <span className="pcf-toggle__thumb" />
                </span>
                <span className="pcf-toggle__label">
                  {form.is_featured ? '⭐ Featured product' : 'Not featured'}
                </span>
              </label>
            </Field>
          </div>
        </Section>

        {/* ── SEO ──────────────────────────────────────────────────── */}
        <Section title="SEO (optional)">
          <Field label="Meta Title" error={errors.meta_title} hint="Defaults to product name if empty">
            <Input
              name="meta_title"
              value={form.meta_title}
              onChange={handleChange}
              placeholder="SEO page title"
              maxLength={70}
            />
          </Field>
          <Field label="Meta Description" error={errors.meta_description}>
            <textarea
              className="pcf-input pcf-textarea pcf-textarea--sm"
              name="meta_description"
              value={form.meta_description}
              onChange={handleChange}
              placeholder="Short description for search engines (max 160 chars)"
              maxLength={160}
              rows={3}
            />
          </Field>
        </Section>

        {/* ── Cache info banner ────────────────────────────────────── */}
        <div className="pcf-cache-note">
          <span className="pcf-cache-note__icon">⚡</span>
          <div>
            <strong>Redis cache behaviour</strong>
            <p>
              {isEditing
                ? 'Saving will fire a post_save signal that deletes product_' + initialProduct.id + ' and all products_list_* keys from Redis.'
                : 'After creation, the product will be served from DB on first fetch, then cached in Redis under product_{id}.'}
            </p>
          </div>
        </div>

        {/* ── Actions ──────────────────────────────────────────────── */}
        <div className="pcf-actions">
          {onCancel && (
            <button
              type="button"
              className="pcf-btn pcf-btn--ghost"
              onClick={onCancel}
              disabled={submitting}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            className="pcf-btn pcf-btn--primary"
            disabled={submitting}
          >
            {submitting
              ? <><span className="pcf-spinner" /> {isEditing ? 'Saving…' : 'Creating…'}</>
              : isEditing ? '💾 Save Changes' : '🚀 Create Product'
            }
          </button>
        </div>

      </form>
    </div>
  )
}