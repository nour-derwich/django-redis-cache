"""
Cache utility functions for products.
Centralized cache management for better maintainability.
"""
from django.core.cache import cache
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def get_cached_product(product_id: int):
    """
    Get product from cache by ID.
    
    Args:
        product_id: Product ID
        
    Returns:
        Product instance or None if not in cache
    """
    from .models.prodect import Product
    
    cache_key = f'product_{product_id}'
    cached_product = cache.get(cache_key)
    
    if cached_product is None:
        try:
            product = Product.objects.select_related('category').get(id=product_id)
            cache.set(cache_key, product, timeout=300)  # 5 minutes
            return product
        except Product.DoesNotExist:
            return None
    
    return cached_product


def get_cached_product_by_slug(slug: str):
    """
    Get product from cache by slug.
    
    Args:
        slug: Product slug
        
    Returns:
        Product instance or None if not found
    """
    from .models.prodect import Product
    
    cache_key = f'product_slug_{slug}'
    cached_product = cache.get(cache_key)
    
    if cached_product is None:
        try:
            product = Product.objects.select_related('category').get(slug=slug)
            cache.set(cache_key, product, timeout=300)
            return product
        except Product.DoesNotExist:
            return None
    
    return cached_product


def get_cached_products_list(filters: dict = None, limit: int = 20):
    """
    Get products list from cache.
    
    Args:
        filters: Dictionary of filters to apply
        limit: Maximum number of products to return
        
    Returns:
        List of Product instances
    """
    from .models.prodect import Product
    
    # Build cache key from filters
    filter_key = '_'.join([f"{k}_{v}" for k, v in sorted((filters or {}).items())])
    cache_key = f'products_list_{filter_key}_{limit}'
    
    cached_products = cache.get(cache_key)
    
    if cached_products is None:
        queryset = Product.objects.select_related('category')
        
        if filters:
            queryset = queryset.filter(**filters)
        
        products = list(queryset[:limit])
        cache.set(cache_key, products, timeout=300)
        return products
    
    return cached_products


def get_cached_category(category_id: int):
    """
    Get category from cache by ID.
    
    Args:
        category_id: Category ID
        
    Returns:
        Category instance or None if not in cache
    """
    from .models.category import Category
    
    cache_key = f'category_{category_id}'
    cached_category = cache.get(cache_key)
    
    if cached_category is None:
        try:
            category = Category.objects.get(id=category_id)
            cache.set(cache_key, category, timeout=300)
            return category
        except Category.DoesNotExist:
            return None
    
    return cached_category


def invalidate_product_cache(product_id: int):
    """
    Invalidate all caches related to a specific product.
    
    Args:
        product_id: Product ID
    """
    from .models.prodect import Product
    
    try:
        product = Product.objects.get(id=product_id)
        product.invalidate_cache()
        logger.info(f"Invalidated cache for product {product_id}")
    except Product.DoesNotExist:
        logger.warning(f"Tried to invalidate cache for non-existent product {product_id}")


def invalidate_product_list_cache():
    """
    Invalidate all product list caches.
    Use after bulk operations or when listing needs refresh.
    """
    patterns = [
        'products_list*',
        'products_page_*',
        'products_featured',
        'products_published',
        'product_statistics',
    ]
    
    for pattern in patterns:
        cache.delete_pattern(pattern)
    
    logger.info("Invalidated all product list caches")


def invalidate_category_cache(category_id: int):
    """
    Invalidate all caches related to a specific category.
    
    Args:
        category_id: Category ID
    """
    from .models.category import Category
    
    try:
        category = Category.objects.get(id=category_id)
        category.invalidate_cache()
        logger.info(f"Invalidated cache for category {category_id}")
    except Category.DoesNotExist:
        logger.warning(f"Tried to invalidate cache for non-existent category {category_id}")


def warm_cache_for_product(product_id: int):
    """
    Pre-warm cache for a specific product.
    Useful for featured products or before marketing campaigns.
    
    Args:
        product_id: Product ID
    """
    from .models.prodect import Product
    
    try:
        product = Product.objects.select_related('category').get(id=product_id)
        cache.set(product.get_cache_key(), product, timeout=300)
        cache.set(product.get_cache_key_by_slug(), product, timeout=300)
        logger.info(f"Warmed cache for product {product_id}")
        return True
    except Product.DoesNotExist:
        logger.warning(f"Tried to warm cache for non-existent product {product_id}")
        return False


def get_cache_statistics():
    """
    Get cache hit/miss statistics.
    Useful for monitoring and optimization.
    
    Returns:
        Dictionary with cache statistics
    """
    from django.core.cache import caches
    
    default_cache = caches['default']
    redis_client = default_cache.client.get_client()
    
    stats = redis_client.info('stats')
    
    return {
        'keyspace_hits': stats.get('keyspace_hits', 0),
        'keyspace_misses': stats.get('keyspace_misses', 0),
        'hit_rate': calculate_hit_rate(stats),
        'total_keys': redis_client.dbsize(),
    }


def calculate_hit_rate(stats: dict) -> float:
    """
    Calculate cache hit rate percentage.
    
    Args:
        stats: Redis stats dictionary
        
    Returns:
        Hit rate as percentage (0-100)
    """
    hits = stats.get('keyspace_hits', 0)
    misses = stats.get('keyspace_misses', 0)
    total = hits + misses
    
    if total == 0:
        return 0.0
    
    return round((hits / total) * 100, 2)


def clear_all_product_caches():
    """
    Clear all product and category related caches.
    Nuclear option - use sparingly!
    """
    patterns = [
        'product_*',
        'products_*',
        'category_*',
        'categories_*',
    ]
    
    for pattern in patterns:
        cache.delete_pattern(pattern)
    
    logger.warning("Cleared ALL product and category caches!")