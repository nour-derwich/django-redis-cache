/**
 * components/CacheStats.js
 * Statistics dashboard — data comes from /api/products/statistics/
 * and is cached by Django for 10 minutes (product_statistics key).
 */
import React from "react";
import CacheBadge from "./CacheBadge";
import { useStatistics } from "../hooks/useProducts";
import "../assets/css/CacheStats.css";

const STAT_CARDS = [
  { key: "total_products", label: "Total", icon: "📦", format: (v) => v },
  {
    key: "published_products",
    label: "Published",
    icon: "✅",
    format: (v) => v,
  },
  { key: "featured_products", label: "Featured", icon: "⭐", format: (v) => v },
  {
    key: "low_stock_products",
    label: "Low Stock",
    icon: "⚠️",
    format: (v) => v,
    warn: true,
  },
  {
    key: "out_of_stock_products",
    label: "Out of Stock",
    icon: "❌",
    format: (v) => v,
    danger: true,
  },
  {
    key: "average_price",
    label: "Avg Price",
    icon: "💰",
    format: (v) => `$${parseFloat(v).toFixed(2)}`,
  },
  {
    key: "total_stock",
    label: "Total Units",
    icon: "🗃️",
    format: (v) => Number(v).toLocaleString(),
  },
  {
    key: "total_value",
    label: "Inventory $",
    icon: "💵",
    format: (v) => `$${parseFloat(v).toLocaleString()}`,
  },
];

export default function CacheStats() {
  const { stats, loading, cacheMeta } = useStatistics();

  return (
    <section className="cache-stats">
      <div className="cache-stats__header">
        <div>
          <h3 className="cache-stats__title">📊 Product Statistics</h3>
          <p className="cache-stats__sub">
            Cached for 10 min · Celery refreshes every 15 min
          </p>
        </div>
        <CacheBadge cacheMeta={cacheMeta} />
      </div>

      {loading && !stats && (
        <div className="cache-stats__loading">
          <div className="spinner" /> Loading stats…
        </div>
      )}

      {stats && (
        <div className="stats-grid">
          {STAT_CARDS.map(({ key, label, icon, format, warn, danger }) => (
            <div
              key={key}
              className={`stat-card ${warn ? "stat-card--warn" : ""} ${danger ? "stat-card--danger" : ""}`}
            >
              <span className="stat-card__icon">{icon}</span>
              <span className="stat-card__value">
                {stats[key] != null ? format(stats[key]) : "—"}
              </span>
              <span className="stat-card__label">{label}</span>
            </div>
          ))}
        </div>
      )}

      <div className="cache-stats__footer">
        ℹ️ Stats served from Redis key <code>product_statistics</code>
      </div>
    </section>
  );
}
