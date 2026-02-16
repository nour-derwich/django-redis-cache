/**
 * components/FilterBar.js
 * Category, status and featured filters for the product list.
 */
import React from "react";
import "../assets/css/FilterBar.css";

export default function FilterBar({ categories, filters, onChange }) {
  const set = (key, value) => {
    const next = { ...filters };
    if (value === "" || value === "all") {
      delete next[key];
    } else {
      next[key] = value;
    }
    onChange(next);
  };

  return (
    <div className="filter-bar">
      {/* Category */}
      <div className="filter-bar__group">
        <label className="filter-bar__label">Category</label>
        <select
          className="filter-bar__select"
          value={filters.category ?? "all"}
          onChange={(e) => set("category", e.target.value)}
        >
          <option value="all">All categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Status */}
      <div className="filter-bar__group">
        <label className="filter-bar__label">Status</label>
        <select
          className="filter-bar__select"
          value={filters.status ?? "all"}
          onChange={(e) => set("status", e.target.value)}
        >
          <option value="all">All statuses</option>
          <option value="published">Published</option>
          <option value="draft">Draft</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* Featured toggle */}
      <div className="filter-bar__group filter-bar__group--check">
        <label className="filter-bar__check">
          <input
            type="checkbox"
            checked={filters.is_featured === "true"}
            onChange={(e) => set("is_featured", e.target.checked ? "true" : "")}
          />
          ⭐ Featured only
        </label>
      </div>

      {/* Reset */}
      {Object.keys(filters).length > 0 && (
        <button className="filter-bar__reset" onClick={() => onChange({})}>
          ✕ Clear filters
        </button>
      )}
    </div>
  );
}
