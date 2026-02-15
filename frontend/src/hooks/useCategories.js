/**
 * hooks/useCategories.js
 */
import { useState, useEffect } from "react";
import { categoriesAPI } from "../services/api";

export function useCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    categoriesAPI
      .list()
      .then((res) => setCategories(res.data.results ?? res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { categories, loading, error };
}
