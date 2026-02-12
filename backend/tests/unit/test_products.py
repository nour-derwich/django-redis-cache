"""
Unit tests — models, properties, cache utils, signals.
No HTTP, no Celery. Pure logic only.
"""
import pytest
from decimal import Decimal
from django.core.cache import cache
from products.models.product import Product
from products.models.category import Category
from products.cache_utils import (
    get_cached_product,
    get_cached_product_by_slug,
    get_cached_products_list,
    get_cached_category,
    invalidate_product_cache,
    invalidate_product_list_cache,
    warm_cache_for_product,
)


# ══════════════════════════════════════════════════════
# MODEL PROPERTIES
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
class TestProductProperties:
    """Test every computed property on the Product model."""

    def test_is_on_sale_true(self, sale_product):
        assert sale_product.is_on_sale is True

    def test_is_on_sale_false_when_no_compare_price(self, product):
        assert product.is_on_sale is False

    def test_is_on_sale_false_when_compare_price_lower(self, db, category):
        """compare_at_price must be GREATER than price to be a sale."""
        p = Product.objects.create(
            name="Wrong Sale",
            slug="wrong-sale",
            sku="WS-001",
            category=category,
            price=Decimal("100.00"),
            compare_at_price=Decimal("80.00"),  # lower — not a sale
            stock_quantity=5,
            status="published",
        )
        assert p.is_on_sale is False

    def test_discount_percentage(self, sale_product):
        # (129.99 - 79.99) / 129.99 * 100 ≈ 38%
        assert sale_product.discount_percentage == 38

    def test_discount_percentage_zero_when_not_on_sale(self, product):
        assert product.discount_percentage == 0

    def test_is_in_stock_true(self, product):
        assert product.is_in_stock is True

    def test_is_in_stock_false(self, out_of_stock_product):
        assert out_of_stock_product.is_in_stock is False

    def test_is_low_stock_false_when_plenty(self, product):
        # stock=50, threshold=10 → NOT low
        assert product.is_low_stock is False

    def test_is_low_stock_true(self, db, category):
        p = Product.objects.create(
            name="Almost Gone",
            slug="almost-gone",
            sku="AG-001",
            category=category,
            price=Decimal("10.00"),
            stock_quantity=3,
            low_stock_threshold=10,
            status="published",
        )
        assert p.is_low_stock is True

    def test_is_low_stock_false_when_out_of_stock(self, out_of_stock_product):
        """0 stock is NOT low-stock, it is out-of-stock."""
        assert out_of_stock_product.is_low_stock is False

    def test_get_cache_key(self, product):
        assert product.get_cache_key() == f"product_{product.id}"

    def test_get_cache_key_by_slug(self, product):
        assert product.get_cache_key_by_slug() == f"product_slug_{product.slug}"


# ══════════════════════════════════════════════════════
# MODEL CRUD
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
class TestProductCRUD:
    """Create / read / update / delete the model directly."""

    def test_create_product(self, product):
        assert product.id is not None
        assert product.name == "Test Laptop"
        assert product.status == "published"

    def test_read_product(self, product):
        fetched = Product.objects.get(id=product.id)
        assert fetched.name == product.name

    def test_update_product(self, product):
        product.price = Decimal("1199.99")
        product.save()
        refreshed = Product.objects.get(id=product.id)
        assert refreshed.price == Decimal("1199.99")

    def test_delete_product(self, product):
        pid = product.id
        product.delete()
        assert not Product.objects.filter(id=pid).exists()

    def test_sku_unique(self, product, db):
        with pytest.raises(Exception):
            Product.objects.create(
                name="Duplicate SKU",
                slug="duplicate-sku",
                sku=product.sku,          # same SKU → must fail
                status="published",
            )

    def test_slug_unique(self, product, db):
        with pytest.raises(Exception):
            Product.objects.create(
                name="Duplicate Slug",
                slug=product.slug,        # same slug → must fail
                sku="UNIQUE-SKU-999",
                status="published",
            )

    def test_increment_view_count(self, product):
        original = product.view_count
        product.increment_view_count()
        product.refresh_from_db()
        assert product.view_count == original + 1


# ══════════════════════════════════════════════════════
# CATEGORY MODEL
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCategoryModel:

    def test_create_category(self, category):
        assert category.id is not None
        assert category.is_active is True

    def test_category_products_relationship(self, product, featured_product, category):
        assert category.products.count() == 2

    def test_category_cache_key(self, category):
        assert category.get_cache_key() == f"category_{category.id}"


# ══════════════════════════════════════════════════════
# CACHE UTILS
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.cache
class TestCacheUtils:
    """Test every function inside cache_utils.py."""

    # ── get_cached_product ──────────────────────────

    def test_get_cached_product_cache_miss_then_hit(self, product):
        """First call hits DB and stores in cache; second call reads from cache."""
        key = product.get_cache_key()

        assert cache.get(key) is None                 # nothing in cache yet

        fetched = get_cached_product(product.id)
        assert fetched.id == product.id               # DB fallback works

        assert cache.get(key) is not None             # now it IS cached

        fetched_again = get_cached_product(product.id)
        assert fetched_again.id == product.id         # served from cache

    def test_get_cached_product_not_found(self):
        result = get_cached_product(99999)
        assert result is None

    # ── get_cached_product_by_slug ──────────────────

    def test_get_cached_product_by_slug(self, product):
        result = get_cached_product_by_slug(product.slug)
        assert result.id == product.id

        slug_key = f"product_slug_{product.slug}"
        assert cache.get(slug_key) is not None

    def test_get_cached_product_by_slug_not_found(self):
        assert get_cached_product_by_slug("non-existent-slug") is None

    # ── get_cached_products_list ────────────────────

    def test_get_cached_products_list(self, product_list):
        products = get_cached_products_list(
            filters={"status": "published"}, limit=10
        )
        assert len(products) == 10

    def test_get_cached_products_list_respects_limit(self, product_list):
        products = get_cached_products_list(limit=3)
        assert len(products) == 3

    def test_get_cached_products_list_caches_result(self, product_list):
        """Second call must hit cache, not DB."""
        get_cached_products_list(filters={"status": "published"}, limit=5)

        # The key format from cache_utils: products_list_{filter_key}_{limit}
        filter_key = "status_published"
        key = f"products_list_{filter_key}_5"
        assert cache.get(key) is not None

    # ── get_cached_category ─────────────────────────

    def test_get_cached_category(self, category):
        result = get_cached_category(category.id)
        assert result.id == category.id
        assert cache.get(f"category_{category.id}") is not None

    def test_get_cached_category_not_found(self):
        assert get_cached_category(99999) is None

    # ── invalidate_product_cache ────────────────────

    def test_invalidate_product_cache(self, product):
        cache.set(product.get_cache_key(), product, 300)
        assert cache.get(product.get_cache_key()) is not None

        invalidate_product_cache(product.id)
        assert cache.get(product.get_cache_key()) is None

    def test_invalidate_nonexistent_product_does_not_raise(self):
        """Should log a warning, not raise an exception."""
        invalidate_product_cache(99999)   # must NOT raise

    # ── invalidate_product_list_cache ───────────────

    def test_invalidate_product_list_cache(self):
        cache.set("products_featured", "data", 300)
        cache.set("products_published", "data", 300)
        cache.set("product_statistics", "data", 300)

        invalidate_product_list_cache()

        assert cache.get("products_featured") is None
        assert cache.get("products_published") is None
        assert cache.get("product_statistics") is None

    # ── warm_cache_for_product ──────────────────────

    def test_warm_cache_for_product(self, product):
        assert cache.get(product.get_cache_key()) is None

        result = warm_cache_for_product(product.id)

        assert result is True
        assert cache.get(product.get_cache_key()) is not None
        assert cache.get(product.get_cache_key_by_slug()) is not None

    def test_warm_cache_for_nonexistent_product(self):
        result = warm_cache_for_product(99999)
        assert result is False


# ══════════════════════════════════════════════════════
# SIGNALS
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
@pytest.mark.cache
class TestCacheSignals:
    """Signals must invalidate cache automatically on every write."""

    def test_cache_cleared_on_product_save(self, product):
        key = product.get_cache_key()
        cache.set(key, product, 300)

        product.price = Decimal("1500.00")
        product.save()                    # signal fires here

        assert cache.get(key) is None

    def test_cache_cleared_on_product_create(self, category):
        """Creating a product should clear list-level caches."""
        cache.set("products_featured", "stale", 300)

        Product.objects.create(
            name="Brand New",
            slug="brand-new",
            sku="BN-001",
            category=category,
            price=Decimal("10.00"),
            status="published",
        )
        # list cache must be gone
        assert cache.get("products_featured") is None

    def test_cache_cleared_on_product_delete(self, product):
        key = product.get_cache_key()
        cache.set(key, product, 300)

        product.delete()                  # signal fires here

        assert cache.get(key) is None

    def test_cache_cleared_on_category_save(self, category):
        key = category.get_cache_key()
        cache.set(key, category, 300)

        category.name = "Updated Electronics"
        category.save()

        assert cache.get(key) is None

    def test_cache_cleared_on_category_delete(self, category):
        key = category.get_cache_key()
        cache.set(key, category, 300)

        category.delete()

        assert cache.get(key) is None