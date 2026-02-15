/**
 * components/CacheBadge.js
 * Reusable pill that shows ⚡ Cached / 🐌 Uncached + response time.
 * Reads the cacheMeta object returned by every API hook.
 */
import React from "react";
import "../assets/css/CacheBadge.css";

export default function CacheBadge({ cacheMeta }) {
  if (!cacheMeta) return null;

  const { hit, responseTime } = cacheMeta;

  return (
    <div className={`cache-badge ${hit ? "hit" : "miss"}`}>
      <span className="cache-badge__icon">{hit ? "⚡" : "🐌"}</span>
      <span className="cache-badge__label">{hit ? "Cached" : "Uncached"}</span>
      {responseTime && (
        <span className="cache-badge__time">{responseTime} ms</span>
      )}
    </div>
  );
}
