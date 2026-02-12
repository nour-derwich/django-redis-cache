# Redis Caching Strategies - Advanced Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Caching Patterns](#caching-patterns)
3. [Implementation Examples](#implementation-examples)
4. [Cache Invalidation](#cache-invalidation)
5. [Performance Optimization](#performance-optimization)
6. [Monitoring & Debugging](#monitoring--debugging)

## Overview

This project demonstrates **6 advanced Redis caching patterns** with Django:

### Implemented Patterns

| Pattern | Use Case | TTL | Invalidation Strategy |
|---------|----------|-----|----------------------|
| View-Level Cache | API endpoints | 60s | Middleware automatic |
| Low-Level Cache | Individual objects | 300s | Signal-based |
| QuerySet Cache | Database queries | 300s | Manual on write |
| List Cache | Paginated results | 60s | Pattern matching |
| Session Cache | User sessions | 24h | Automatic expiry |
| Statistics Cache | Aggregations | 600s | Celery warmup |

## Caching Patterns

### 1. View-Level Caching

**When to use**: Full API response caching when content doesn't change frequently.

**Implementation**:
```python
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class ProductViewSet(viewsets.ModelViewSet):
    @method_decorator(cache_page(60))
    def list(self, request):
        # Returns cached response for 60 seconds
        return super().list(request)
```

**Pros**:
- Fastest response time
- Minimal code changes
- Automatic cache key generation

**Cons**:
- Less control over invalidation
- Can serve stale data
- Cache varies by full URL

**Best for**: Public read-only endpoints with low update frequency.

---

### 2. Low-Level Cache API

**When to use**: Fine-grained control over what gets cached and when.

**Implementation**:
```python
from django.core.cache import cache

def get_product(product_id):
    cache_key = f'product_{product_id}'
    product = cache.get(cache_key)
    
    if product is None:
        product = Product.objects.get(id=product_id)
        cache.set(cache_key, product, timeout=300)
    
    return product
```

**Pros**:
- Full control over cache keys
- Selective caching
- Easy to invalidate

**Cons**:
- More boilerplate code
- Manual cache management
- Need to handle cache misses

**Best for**: Individual object caching, complex business logic.

---

### 3. QuerySet Caching

**When to use**: Expensive database queries that return the same results frequently.

**Implementation**:
```python
def get_featured_products():
    cache_key = 'featured_products'
    products = cache.get(cache_key)
    
    if products is None:
        products = list(Product.objects.filter(
            is_featured=True
        ).select_related('category')[:10])
        cache.set(cache_key, products, timeout=300)
    
    return products
```

**Pros**:
- Reduces database load
- Works with complex queries
- Can cache relationships

**Cons**:
- Must convert QuerySet to list
- Memory overhead
- Need to handle updates

**Best for**: Complex queries with joins, aggregations, filters.

---

### 4. Template Fragment Caching

**When to use**: Caching parts of rendered templates.

**Implementation**:
```django
{% load cache %}
{% cache 500 product_sidebar %}
    <!-- Expensive sidebar render -->
    {% for product in featured_products %}
        ...
    {% endfor %}
{% endcache %}
```

**Pros**:
- Cache expensive renders
- Granular control
- Template-level caching

**Cons**:
- Template-specific
- Requires template tags
- Harder to invalidate

**Best for**: Sidebars, widgets, repeated template sections.

---

### 5. Per-Site Cache (Middleware)

**When to use**: Cache entire pages for anonymous users.

**Implementation**:
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',  # First
    # ... other middleware ...
    'django.middleware.cache.FetchFromCacheMiddleware',  # Last
]

CACHE_MIDDLEWARE_SECONDS = 60
```

**Pros**:
- Zero code changes
- Fastest for static sites
- Automatic cache headers

**Cons**:
- All-or-nothing caching
- Can't cache authenticated users
- Hard to debug

**Best for**: Mostly static sites, documentation, blogs.

---

### 6. Session Caching

**When to use**: Store user session data in Redis instead of database.

**Implementation**:
```python
# settings.py
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

CACHES = {
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/3',
        'TIMEOUT': 86400,  # 24 hours
    }
}
```

**Pros**:
- Faster than database sessions
- Automatic expiry
- Scales horizontally

**Cons**:
- Data lost on cache flush
- Requires Redis availability
- Potential data loss

**Best for**: High-traffic sites, session-heavy applications.

---

## Implementation Examples

### Example 1: Caching Product List with Filters

```python
def get_products_list(filters=None, page=1):
    """
    Get products with filters and pagination.
    Cache key includes all filters for granular caching.
    """
    # Build cache key from filters
    filter_hash = hash(frozenset((filters or {}).items()))
    cache_key = f'products_list_{filter_hash}_page_{page}'
    
    # Try cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Query database
    queryset = Product.objects.select_related('category')
    if filters:
        queryset = queryset.filter(**filters)
    
    # Paginate
    paginator = Paginator(queryset, 20)
    products = paginator.page(page)
    
    # Cache for 5 minutes
    cache.set(cache_key, products, timeout=300)
    
    return products
```

### Example 2: Smart Cache Invalidation

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Product)
def invalidate_product_caches(sender, instance, **kwargs):
    """
    Invalidate multiple cache levels when product changes.
    """
    # Individual product cache
    cache.delete(f'product_{instance.id}')
    cache.delete(f'product_slug_{instance.slug}')
    
    # List caches
    cache.delete_pattern('products_list_*')
    
    # Category caches
    if instance.category:
        cache.delete(f'category_{instance.category.id}_products')
    
    # Statistics cache
    cache.delete('product_statistics')
```

### Example 3: Cache Warming with Celery

```python
from celery import shared_task

@shared_task
def warm_product_cache():
    """
    Pre-populate cache for popular products.
    Runs every 5 minutes.
    """
    # Get featured products
    products = Product.objects.filter(
        is_featured=True,
        status='published'
    ).select_related('category')[:20]
    
    # Warm cache
    for product in products:
        cache.set(
            f'product_{product.id}',
            product,
            timeout=600  # 10 minutes
        )
    
    return f'Warmed {len(products)} products'
```

## Cache Invalidation

### Invalidation Strategies

1. **Time-based (TTL)**: Let cache expire naturally
2. **Event-based**: Invalidate on model changes (signals)
3. **Manual**: Explicit cache clearing
4. **Pattern matching**: Clear multiple keys at once

### When to Invalidate

| Event | Invalidation Strategy | Example |
|-------|----------------------|---------|
| Product Created | Clear list caches | `cache.delete_pattern('products_list_*')` |
| Product Updated | Clear object + lists | `cache.delete(f'product_{id}')` |
| Product Deleted | Clear all related | `instance.invalidate_cache()` |
| Bulk Import | Clear everything | `cache.clear()` |

## Performance Optimization

### 1. Use Connection Pooling

```python
CACHES = {
    'default': {
        'OPTIONS': {
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}
```

### 2. Enable Compression

```python
CACHES = {
    'default': {
        'OPTIONS': {
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        }
    }
}
```

### 3. Use HiredisParser

```python
CACHES = {
    'default': {
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    }
}
```

### 4. Optimal TTL Values

| Data Type | Recommended TTL | Reasoning |
|-----------|----------------|-----------|
| Static content | 3600s (1h) | Rarely changes |
| Product lists | 300s (5m) | Moderate changes |
| Product details | 600s (10m) | Low change frequency |
| User sessions | 86400s (24h) | Long-lived |
| Statistics | 900s (15m) | Regenerated regularly |

## Monitoring & Debugging

### Check Cache Statistics

```python
from django.core.cache import caches

def get_cache_stats():
    cache = caches['default']
    client = cache.client.get_client()
    
    info = client.info('stats')
    
    return {
        'hits': info['keyspace_hits'],
        'misses': info['keyspace_misses'],
        'hit_rate': (info['keyspace_hits'] / 
                    (info['keyspace_hits'] + info['keyspace_misses']) * 100),
        'total_keys': client.dbsize(),
    }
```

### View All Cache Keys

```bash
# Connect to Redis
docker-compose exec redis redis-cli -a redispass

# List all keys
KEYS *

# View specific key
GET redis_demo:product_123

# Delete pattern
EVAL "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" 0 "products_*"
```

### Performance Testing

```python
import time
from django.core.cache import cache

def benchmark_cache():
    """Compare cache vs database performance."""
    
    # Cache test
    start = time.time()
    for i in range(1000):
        cache.get(f'test_key_{i}')
    cache_time = time.time() - start
    
    # Database test
    start = time.time()
    for i in range(1000):
        Product.objects.get(id=i)
    db_time = time.time() - start
    
    print(f'Cache: {cache_time:.2f}s')
    print(f'Database: {db_time:.2f}s')
    print(f'Speedup: {db_time/cache_time:.2f}x')
```

## Best Practices

1. **Always set TTL**: Never cache indefinitely
2. **Use consistent key naming**: `{app}:{model}:{id}:{field}`
3. **Invalidate on write**: Update cache when data changes
4. **Monitor hit rates**: Aim for >80% hit rate
5. **Warm critical caches**: Pre-populate on startup
6. **Handle cache failures**: Graceful degradation
7. **Version cache keys**: For schema changes
8. **Use separate Redis DBs**: Different data types
9. **Compress large values**: Save memory
10. **Log cache operations**: For debugging

## Common Pitfalls

❌ **Don't**: Cache forever without TTL
✅ **Do**: Set appropriate TTL based on data volatility

❌ **Don't**: Cache without invalidation strategy
✅ **Do**: Plan invalidation before implementing

❌ **Don't**: Cache everything
✅ **Do**: Profile and cache what matters

❌ **Don't**: Ignore cache failures
✅ **Do**: Implement fallback to database

❌ **Don't**: Use cache as database
✅ **Do**: Treat cache as optimization layer

## Advanced Topics

### Multi-Level Caching

Combine multiple cache layers:

```python
def get_product(product_id):
    # L1: In-memory cache (fastest)
    if product_id in _local_cache:
        return _local_cache[product_id]
    
    # L2: Redis cache
    cache_key = f'product_{product_id}'
    product = cache.get(cache_key)
    if product:
        _local_cache[product_id] = product
        return product
    
    # L3: Database (slowest)
    product = Product.objects.get(id=product_id)
    cache.set(cache_key, product, 300)
    _local_cache[product_id] = product
    
    return product
```

### Cache Stampede Prevention

Prevent simultaneous cache misses:

```python
import threading

_locks = {}

def get_product_safe(product_id):
    cache_key = f'product_{product_id}'
    
    # Try cache first
    product = cache.get(cache_key)
    if product:
        return product
    
    # Acquire lock for this key
    lock = _locks.setdefault(product_id, threading.Lock())
    
    with lock:
        # Double-check cache
        product = cache.get(cache_key)
        if product:
            return product
        
        # Query database (only one thread does this)
        product = Product.objects.get(id=product_id)
        cache.set(cache_key, product, 300)
        
        return product
```

---

**For more examples, see the codebase implementation in `products/views.py`, `products/cache_utils.py`, and `products/tasks.py`.**
