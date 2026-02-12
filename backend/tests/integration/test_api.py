"""
Integration tests — HTTP layer, API endpoints, cache interaction.
Tests real DRF views hitting a real test DB and a real Redis.
"""
import pytest
from decimal import Decimal
from django.core.cache import cache
from django.urls import reverse


# ══════════════════════════════════════════════════════
# PRODUCT LIST  GET /api/products/
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.integration
class TestProductListEndpoint:

    def test_list_returns_200(self, api_client, product):
        response = api_client.get("/api/products/")
        assert response.status_code == 200

    def test_list_contains_published_product(self, api_client, product):
        response = api_client.get("/api/products/")
        ids = [p["id"] for p in response.data["results"]]
        assert product.id in ids

    def test_list_hides_draft_from_anonymous(self, api_client, draft_product):
        """Anonymous users must NOT see draft products."""
        response = api_client.get("/api/products/")
        ids = [p["id"] for p in response.data["results"]]
        assert draft_product.id not in ids

    def test_list_shows_draft_to_staff(self, admin_client, draft_product):
        """Staff users CAN see draft products."""
        response = admin_client.get("/api/products/")
        ids = [p["id"] for p in response.data["results"]]
        assert draft_product.id in ids

    def test_list_response_is_cached(self, api_client, product):
        """Second identical request must be served from cache."""
        api_client.get("/api/products/")               # cache MISS
        api_client.get("/api/products/")               # cache HIT

        # The view stores data with key products_list_{hash}
        # We just verify at least one products_list_* key exists in Redis
        from django.core.cache import caches
        redis = caches["default"].client.get_client()
        keys = redis.keys("*products_list*")
        assert len(keys) > 0

    def test_list_filter_by_status(self, api_client, product, draft_product, admin_client):
        response = admin_client.get("/api/products/?status=draft")
        ids = [p["id"] for p in response.data["results"]]
        assert draft_product.id in ids
        assert product.id not in ids

    def test_list_filter_by_featured(self, api_client, product, featured_product):
        response = api_client.get("/api/products/?is_featured=true")
        ids = [p["id"] for p in response.data["results"]]
        assert featured_product.id in ids
        assert product.id not in ids

    def test_list_pagination(self, api_client, product_list):
        response = api_client.get("/api/products/")
        assert "results" in response.data
        assert "count" in response.data
        assert response.data["count"] == 10


# ══════════════════════════════════════════════════════
# PRODUCT DETAIL  GET /api/products/{id}/
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.integration
class TestProductDetailEndpoint:

    def test_detail_returns_200(self, api_client, product):
        response = api_client.get(f"/api/products/{product.id}/")
        assert response.status_code == 200

    def test_detail_returns_correct_product(self, api_client, product):
        response = api_client.get(f"/api/products/{product.id}/")
        assert response.data["id"] == product.id
        assert response.data["name"] == product.name

    def test_detail_404_for_missing_product(self, api_client):
        response = api_client.get("/api/products/99999/")
        assert response.status_code == 404

    def test_detail_is_cached_after_first_request(self, api_client, product):
        api_client.get(f"/api/products/{product.id}/")      # MISS → stores in cache
        assert cache.get(product.get_cache_key()) is not None

    def test_detail_served_from_cache(self, api_client, product):
        """Manually put stale name in cache — API must return it."""
        stale = product
        stale.name = "Cached Name"
        cache.set(product.get_cache_key(), stale, 300)

        response = api_client.get(f"/api/products/{product.id}/")
        assert response.data["name"] == "Cached Name"

    def test_detail_increments_view_count(self, api_client, product):
        original = product.view_count
        api_client.get(f"/api/products/{product.id}/")
        product.refresh_from_db()
        assert product.view_count == original + 1


# ══════════════════════════════════════════════════════
# PRODUCT CREATE  POST /api/products/
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.integration
class TestProductCreateEndpoint:

    def test_create_requires_auth(self, api_client, category):
        payload = {
            "name": "New Product",
            "slug": "new-product",
            "sku": "NEW-001",
            "description": "desc",
            "category": category.id,
            "price": "49.99",
            "stock_quantity": 10,
            "status": "published",
        }
        response = api_client.post("/api/products/", payload)
        assert response.status_code in (401, 403)

    def test_create_success_as_staff(self, admin_client, category):
        payload = {
            "name": "New Product",
            "slug": "new-product",
            "sku": "NEW-001",
            "description": "A new product",
            "category": category.id,
            "price": "49.99",
            "stock_quantity": 10,
            "status": "published",
        }
        response = admin_client.post("/api/products/", payload, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "New Product"

    def test_create_invalidates_list_cache(self, admin_client, category):
        """After creating, stale list caches must be gone."""
        cache.set("products_featured", "stale_data", 300)

        payload = {
            "name": "Cache-Buster Product",
            "slug": "cache-buster",
            "sku": "CB-001",
            "description": "desc",
            "category": category.id,
            "price": "9.99",
            "stock_quantity": 5,
            "status": "published",
        }
        admin_client.post("/api/products/", payload, format="json")

        assert cache.get("products_featured") is None

    def test_create_duplicate_sku_returns_400(self, admin_client, product, category):
        payload = {
            "name": "Dup SKU",
            "slug": "dup-sku",
            "sku": product.sku,         # duplicate
            "description": "desc",
            "category": category.id,
            "price": "9.99",
            "stock_quantity": 1,
            "status": "published",
        }
        response = admin_client.post("/api/products/", payload, format="json")
        assert response.status_code == 400


# ══════════════════════════════════════════════════════
# PRODUCT UPDATE  PUT/PATCH /api/products/{id}/
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.integration
class TestProductUpdateEndpoint:

    def test_partial_update_success(self, admin_client, product):
        response = admin_client.patch(
            f"/api/products/{product.id}/",
            {"price": "1299.99"},
            format="json"
        )
        assert response.status_code == 200

    def test_update_invalidates_cache(self, admin_client, product):
        cache.set(product.get_cache_key(), product, 300)
        assert cache.get(product.get_cache_key()) is not None

        admin_client.patch(
            f"/api/products/{product.id}/",
            {"price": "1299.99"},
            format="json"
        )
        # signal must clear it
        assert cache.get(product.get_cache_key()) is None

    def test_update_requires_auth(self, api_client, product):
        response = api_client.patch(
            f"/api/products/{product.id}/",
            {"price": "1.00"},
            format="json"
        )
        assert response.status_code in (401, 403)


# ══════════════════════════════════════════════════════
# PRODUCT DELETE  DELETE /api/products/{id}/
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.integration
class TestProductDeleteEndpoint:

    def test_delete_success(self, admin_client, product):
        response = admin_client.delete(f"/api/products/{product.id}/")
        assert response.status_code == 204

    def test_delete_invalidates_cache(self, admin_client, product):
        cache.set(product.get_cache_key(), product, 300)

        admin_client.delete(f"/api/products/{product.id}/")

        assert cache.get(product.get_cache_key()) is None

    def test_delete_requires_auth(self, api_client, product):
        response = api_client.delete(f"/api/products/{product.id}/")
        assert response.status_code in (401, 403)


# ══════════════════════════════════════════════════════
# CUSTOM ACTIONS
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.integration
class TestProductCustomActions:

    def test_featured_returns_only_featured(self, api_client, product, featured_product):
        response = api_client.get("/api/products/featured/")
        assert response.status_code == 200
        ids = [p["id"] for p in response.data]
        assert featured_product.id in ids
        assert product.id not in ids

    def test_featured_is_cached(self, api_client, featured_product):
        api_client.get("/api/products/featured/")
        assert cache.get("products_featured") is not None

    def test_statistics_returns_correct_counts(self, api_client, product, draft_product):
        response = api_client.get("/api/products/statistics/")
        assert response.status_code == 200
        assert response.data["total_products"] >= 2
        assert response.data["published_products"] >= 1

    def test_statistics_is_cached(self, api_client, product):
        api_client.get("/api/products/statistics/")
        assert cache.get("product_statistics") is not None

    def test_clear_cache_requires_staff(self, auth_client):
        response = auth_client.post("/api/products/clear_cache/")
        assert response.status_code == 403

    def test_clear_cache_as_staff(self, admin_client):
        cache.set("products_featured", "data", 300)
        response = admin_client.post("/api/products/clear_cache/")
        assert response.status_code == 200
        assert cache.get("products_featured") is None

    def test_cache_info_requires_staff(self, auth_client):
        response = auth_client.get("/api/products/cache_info/")
        assert response.status_code == 403

    def test_cache_info_as_staff(self, admin_client):
        response = admin_client.get("/api/products/cache_info/")
        assert response.status_code == 200
        assert "total_keys" in response.data


# ══════════════════════════════════════════════════════
# CATEGORY ENDPOINTS
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.integration
class TestCategoryEndpoints:

    def test_list_categories(self, api_client, category):
        response = api_client.get("/api/categories/")
        assert response.status_code == 200

    def test_list_categories_cached(self, api_client, category):
        api_client.get("/api/categories/")
        assert cache.get("categories_list") is not None

    def test_retrieve_category_by_slug(self, api_client, category):
        response = api_client.get(f"/api/categories/{category.slug}/")
        assert response.status_code == 200
        assert response.data["slug"] == category.slug

    def test_retrieve_category_caches_instance(self, api_client, category):
        api_client.get(f"/api/categories/{category.slug}/")
        assert cache.get(f"category_slug_{category.slug}") is not None

    def test_category_products_action(self, api_client, product, category):
        response = api_client.get(f"/api/categories/{category.slug}/products/")
        assert response.status_code == 200
        ids = [p["id"] for p in response.data]
        assert product.id in ids

    def test_category_products_are_cached(self, api_client, product, category):
        api_client.get(f"/api/categories/{category.slug}/products/")
        assert cache.get(f"category_{category.id}_products") is not None