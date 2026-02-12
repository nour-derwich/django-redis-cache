"""
Test script for cache invalidation signals.
Run with: docker-compose exec backend python test_signals.py
"""
from django.core.cache import cache
from products.models import Product, Category

def test_product_signals():
    print("Testing Product signals...")
    
    # Create a product
    product = Product.objects.create(
        name="Test Product",
        slug="test-product-signal",
        sku="TEST-SIGNAL-001",
        price=99.99,
        status='published'
    )
    
    # Cache it
    cache_key = f'product_{product.id}'
    cache.set(cache_key, product, 300)
    
    assert cache.get(cache_key) is not None, "❌ Failed to cache product"
    print("✅ Product cached successfully")
    
    # Update product (should trigger signal and invalidate cache)
    product.price = 199.99
    product.save()
    
    assert cache.get(cache_key) is None, "❌ Cache not invalidated on save"
    print("✅ Cache invalidated on product save")
    
    # Delete product
    product_id = product.id
    cache.set(cache_key, product, 300)
    product.delete()
    
    assert cache.get(cache_key) is None, "❌ Cache not invalidated on delete"
    print("✅ Cache invalidated on product delete")

def test_category_signals():
    print("\nTesting Category signals...")
    
    category = Category.objects.create(
        name="Test Category",
        slug="test-category-signal"
    )
    
    cache_key = f'category_{category.id}'
    cache.set(cache_key, category, 300)
    
    assert cache.get(cache_key) is not None, "❌ Failed to cache category"
    print("✅ Category cached successfully")
    
    # Update category
    category.name = "Updated Category"
    category.save()
    
    assert cache.get(cache_key) is None, "❌ Cache not invalidated on save"
    print("✅ Cache invalidated on category save")
    
    category.delete()
    print("✅ Category deleted successfully")

if __name__ == '__main__':
    test_product_signals()
    test_category_signals()
    print("\n🎉 All signal tests passed!")