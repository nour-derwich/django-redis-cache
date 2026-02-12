"""
Unit tests for Product models and caching.
"""
import pytest
from decimal import Decimal
from django.core.cache import cache
from products.models import Product, Category
from products.cache_utils import (
    get_cached_product,
    get_cached_products_list,
    invalidate_product_cache,
)


@pytest.mark.django_db
@pytest.mark.cache
class TestProductModel:
    """Test Product model functionality."""
    
    def test_create_product(self):
        """Test creating a product."""
        category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )
        
        product = Product.objects.create(
            name="Test Laptop",
            slug="test-laptop",
            sku="TEST-001",
            description="A test laptop",
            category=category,
            price=Decimal("999.99"),
            stock_quantity=50,
            status='published'
        )
        
        assert product.id is not None
        assert product.name == "Test Laptop"
        assert product.category == category
    
    def test_product_is_on_sale(self):
        """Test is_on_sale property."""
        product = Product.objects.create(
            name="Sale Product",
            slug="sale-product",
            sku="SALE-001",
            price=Decimal("99.99"),
            compare_at_price=Decimal("149.99"),
            status='published'
        )
        
        assert product.is_on_sale is True
        assert product.discount_percentage == 33
    
    def test_product_stock_status(self):
        """Test stock status properties."""
        # In stock
        product1 = Product.objects.create(
            name="In Stock",
            slug="in-stock",
            sku="STOCK-001",
            stock_quantity=100,
            low_stock_threshold=10,
            status='published'
        )
        assert product1.is_in_stock is True
        assert product1.is_low_stock is False
        
        # Low stock
        product2 = Product.objects.create(
            name="Low Stock",
            slug="low-stock",
            sku="STOCK-002",
            stock_quantity=5,
            low_stock_threshold=10,
            status='published'
        )
        assert product2.is_in_stock is True
        assert product2.is_low_stock is True
        
        # Out of stock
        product3 = Product.objects.create(
            name="Out of Stock",
            slug="out-stock",
            sku="STOCK-003",
            stock_quantity=0,
            status='published'
        )
        assert product3.is_in_stock is False


@pytest.mark.django_db
@pytest.mark.cache
class TestProductCaching:
    """Test caching functionality."""
    
    def test_get_cached_product(self):
        """Test getting product from cache."""
        product = Product.objects.create(
            name="Cached Product",
            slug="cached-product",
            sku="CACHE-001",
            price=Decimal("99.99"),
            status='published'
        )
        
        # First call - should cache
        cached_product = get_cached_product(product.id)
        assert cached_product.id == product.id
        
        # Verify it's in cache
        cache_key = f'product_{product.id}'
        assert cache.get(cache_key) is not None
    
    def test_cache_invalidation_on_save(self):
        """Test cache invalidation when product is saved."""
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            sku="TEST-002",
            price=Decimal("99.99"),
            status='published'
        )
        
        # Cache the product
        cache_key = f'product_{product.id}'
        cache.set(cache_key, product, timeout=300)
        assert cache.get(cache_key) is not None
        
        # Update product (should invalidate cache via signal)
        product.price = Decimal("199.99")
        product.save()
        
        # Cache should be cleared
        assert cache.get(cache_key) is None
    
    def test_cache_invalidation_on_delete(self):
        """Test cache invalidation when product is deleted."""
        product = Product.objects.create(
            name="Delete Test",
            slug="delete-test",
            sku="DELETE-001",
            status='published'
        )
        
        # Cache the product
        cache_key = f'product_{product.id}'
        cache.set(cache_key, product, timeout=300)
        
        # Delete product
        product_id = product.id
        product.delete()
        
        # Cache should be cleared
        assert cache.get(cache_key) is None
    
    def test_get_cached_products_list(self):
        """Test getting product list from cache."""
        # Create test products
        for i in range(5):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                sku=f"PRD-{i:03d}",
                status='published'
            )
        
        # Get products (should cache)
        products = get_cached_products_list(
            filters={'status': 'published'},
            limit=5
        )
        
        assert len(products) == 5


@pytest.mark.django_db
class TestCategoryModel:
    """Test Category model."""
    
    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            description="A test category"
        )
        
        assert category.id is not None
        assert category.name == "Test Category"
        assert category.is_active is True
    
    def test_category_product_relationship(self):
        """Test category-product relationship."""
        category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )
        
        product1 = Product.objects.create(
            name="Laptop",
            slug="laptop",
            sku="LAP-001",
            category=category,
            status='published'
        )
        
        product2 = Product.objects.create(
            name="Phone",
            slug="phone",
            sku="PHN-001",
            category=category,
            status='published'
        )
        
        assert category.products.count() == 2
        assert product1 in category.products.all()
        assert product2 in category.products.all()