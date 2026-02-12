"""
Celery task tests — run tasks synchronously with CELERY_TASK_ALWAYS_EAGER.
Tests warm_product_cache, generate_cache_statistics, process_bulk_import, etc.
"""
import pytest
from decimal import Decimal
from django.core.cache import cache
from unittest.mock import patch


# ══════════════════════════════════════════════════════
# SETUP: Run Celery tasks synchronously in tests
# ══════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def celery_eager(settings):
    """
    Force every Celery task to run synchronously inside the test process.
    No broker needed — results are returned directly.
    """
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


# ══════════════════════════════════════════════════════
# warm_product_cache
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.celery
class TestWarmProductCache:

    def test_warms_featured_products(self, featured_product):
        from products.tasks import warm_product_cache
        result = warm_product_cache()

        assert result["products_warmed"] >= 1
        # Cache must now hold the featured product
        assert cache.get(featured_product.get_cache_key()) is not None

    def test_warms_categories(self, category, product):
        from products.tasks import warm_product_cache
        result = warm_product_cache()

        assert result["categories_warmed"] >= 1
        assert cache.get(f"category_{category.id}") is not None

    def test_returns_correct_structure(self, featured_product):
        from products.tasks import warm_product_cache
        result = warm_product_cache()

        assert "products_warmed" in result
        assert "categories_warmed" in result
        assert isinstance(result["products_warmed"], int)
        assert isinstance(result["categories_warmed"], int)

    def test_works_when_no_featured_products(self, product):
        """Non-featured products should still warm category caches."""
        from products.tasks import warm_product_cache
        result = warm_product_cache()

        # No featured products — products_warmed should be 0
        assert result["products_warmed"] == 0
        # But categories should still be warmed
        assert result["categories_warmed"] >= 1


# ══════════════════════════════════════════════════════
# generate_cache_statistics
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.celery
class TestGenerateCacheStatistics:

    def test_stores_stats_in_cache(self, product, draft_product):
        from products.tasks import generate_cache_statistics
        generate_cache_statistics()

        stats = cache.get("product_statistics")
        assert stats is not None

    def test_correct_totals(self, product, draft_product):
        from products.tasks import generate_cache_statistics
        result = generate_cache_statistics()

        assert result["total_products"] == 2
        assert result["published_products"] == 1
        assert result["draft_products"] == 1

    def test_stats_contain_all_keys(self, product):
        from products.tasks import generate_cache_statistics
        result = generate_cache_statistics()

        required_keys = [
            "total_products", "published_products", "draft_products",
            "archived_products", "total_stock", "low_stock_products",
            "out_of_stock_products", "featured_products",
            "average_price", "total_value",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_zero_counts_on_empty_db(self, db):
        from products.tasks import generate_cache_statistics
        result = generate_cache_statistics()

        assert result["total_products"] == 0
        assert result["published_products"] == 0


# ══════════════════════════════════════════════════════
# process_bulk_import
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.celery
class TestProcessBulkImport:

    def _payload(self, n=3, category=None):
        """Build a list of valid product dicts."""
        items = []
        for i in range(n):
            items.append({
                "name": f"Import Product {i}",
                "slug": f"import-product-{i}",
                "sku": f"IMP-{i:03d}",
                "description": "Imported",
                "price": Decimal("29.99"),
                "stock_quantity": 10,
                "status": "published",
            })
            if category:
                items[-1]["category"] = category
        return items

    def test_creates_new_products(self, db, category):
        from products.tasks import process_bulk_import
        result = process_bulk_import(self._payload(3))

        assert result["created"] == 3
        assert result["errors"] == 0

    def test_updates_existing_products(self, db, category, product):
        from products.tasks import process_bulk_import
        # Re-import same SKU with a new name
        payload = [{
            "name": "Updated Name",
            "slug": product.slug,
            "sku": product.sku,
            "description": "Updated",
            "price": Decimal("200.00"),
            "stock_quantity": 99,
            "status": "published",
        }]
        result = process_bulk_import(payload)

        assert result["updated"] == 1
        assert result["created"] == 0

    def test_invalidates_caches_after_import(self, db):
        from products.tasks import process_bulk_import
        cache.set("products_featured", "stale", 300)

        process_bulk_import(self._payload(2))

        assert cache.get("products_featured") is None

    def test_returns_summary_dict(self, db):
        from products.tasks import process_bulk_import
        result = process_bulk_import(self._payload(2))

        assert "created" in result
        assert "updated" in result
        assert "errors" in result
        assert "total" in result
        assert result["total"] == 2


# ══════════════════════════════════════════════════════
# sync_inventory
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.celery
class TestSyncInventory:

    def test_updates_stock_quantity(self, product):
        from products.tasks import sync_inventory
        result = sync_inventory({product.sku: 999})

        product.refresh_from_db()
        assert product.stock_quantity == 999
        assert result["updated"] == 1

    def test_skips_unknown_sku(self, db):
        from products.tasks import sync_inventory
        result = sync_inventory({"NONEXISTENT-SKU": 50})

        # No crash — just 0 updated
        assert result["updated"] == 0

    def test_bulk_update(self, product, featured_product):
        from products.tasks import sync_inventory
        result = sync_inventory({
            product.sku: 111,
            featured_product.sku: 222,
        })

        assert result["updated"] == 2
        product.refresh_from_db()
        featured_product.refresh_from_db()
        assert product.stock_quantity == 111
        assert featured_product.stock_quantity == 222


# ══════════════════════════════════════════════════════
# update_product_prices
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.celery
class TestUpdateProductPrices:

    def test_updates_price(self, product):
        from products.tasks import update_product_prices
        result = update_product_prices({str(product.id): Decimal("1.00")})

        product.refresh_from_db()
        assert product.price == Decimal("1.00")
        assert result["updated"] == 1

    def test_skips_missing_id(self, db):
        from products.tasks import update_product_prices
        result = update_product_prices({"99999": Decimal("1.00")})
        assert result["updated"] == 0


# ══════════════════════════════════════════════════════
# cleanup_expired_cache
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.celery
class TestCleanupExpiredCache:

    def test_returns_stats_dict(self, db):
        from products.tasks import cleanup_expired_cache

        # Patch get_cache_statistics so we don't need a live Redis in CI
        with patch("products.tasks.get_cache_statistics") as mock_stats:
            mock_stats.return_value = {
                "keyspace_hits": 100,
                "keyspace_misses": 10,
                "hit_rate": 90.0,
                "total_keys": 5,
            }
            result = cleanup_expired_cache()

        assert "keyspace_hits" in result
        assert result["hit_rate"] == 90.0