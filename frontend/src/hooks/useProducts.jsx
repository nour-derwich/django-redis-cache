/**
 * hooks/useProducts.js
 * Fetches the product list and exposes cache metadata.
 */
import { useState, useEffect, useCallback } from "react";
import { productsAPI } from "../services/api";

export function useProducts(filters = {}) {
  const [products, setProducts] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [cacheMeta, setCacheMeta] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await productsAPI.list(filters);
      setProducts(res.data.results ?? res.data);
      setTotalCount(res.data.count ?? 0);
      setCacheMeta(res.cacheMeta);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]); // eslint-disable-line

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { products, totalCount, loading, error, cacheMeta, refetch: fetch };
}

export function useProductDetail(id) {
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [cacheMeta, setCacheMeta] = useState(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    productsAPI
      .detail(id)
      .then((res) => {
        setProduct(res.data);
        setCacheMeta(res.cacheMeta);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  return { product, loading, error, cacheMeta };
}

export function useFeaturedProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cacheMeta, setCacheMeta] = useState(null);

  useEffect(() => {
    productsAPI
      .featured()
      .then((res) => {
        setProducts(res.data);
        setCacheMeta(res.cacheMeta);
      })
      .finally(() => setLoading(false));
  }, []);

  return { products, loading, cacheMeta };
}

// export function useStatistics() {
//   const [stats, setStats] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [cacheMeta, setCacheMeta] = useState(null);

//   const fetch = useCallback(() => {
//     setLoading(true);
//     productsAPI
//       .statistics()
//       .then((res) => {
//         setStats(res.data);
//         setCacheMeta(res.cacheMeta);
//       })
//       .finally(() => setLoading(false));
//   }, []);

//   useEffect(() => {
//     fetch();
//     const interval = setInterval(fetch, 15000); // re-poll every 15 s
//     return () => clearInterval(interval);
//   }, [fetch]);

//   return { stats, loading, cacheMeta };
// }
export function useStatistics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [cacheMeta, setCacheMeta] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await productsAPI.statistics();
      setStats(res.data);
      setCacheMeta(res.cacheMeta);
      setError(null);
    } catch (err) {
      // Don't wipe existing stats on a failed refresh
      setError(err.response?.data?.detail ?? err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    // Slow the poll way down — statistics don't need 15-second refresh.
    // Remove the interval entirely if real-time data isn't required.
    const interval = setInterval(fetch, 5 * 60 * 1000); // every 5 minutes
    return () => clearInterval(interval);
  }, [fetch]);

  return { stats, loading, error, cacheMeta, refetch: fetch };
}