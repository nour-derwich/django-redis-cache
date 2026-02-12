"""
Celery tasks for cache warming and async operations.
Demonstrates scheduled tasks and async data processing.
"""
from celery import shared_task
from django.core.cache import cache
from django.db.models import Sum, Avg, Count
from .models.prodect import Product
from .models.category import Category
from .cache_utils import (
    warm_cache_for_product,
    get_cache_statistics,
    clear_all_product_caches
)
import logging

logger = logging.getLogger(__name__)


@shared_task(name='products.tasks.warm_product_cache')
def warm_product_cache():
    """
    Warm cache for most popular and featured products.
    Runs every 5 minutes via Celery Beat.
    """
    logger.info("Starting cache warming task...")
    
    # Warm cache for featured products
    featured_products = Product.objects.filter(
        is_featured=True,
        status='published'
    ).select_related('category')[:20]
    
    warmed_count = 0
    for product in featured_products:
        cache.set(product.get_cache_key(), product, timeout=600)  # 10 minutes
        cache.set(product.get_cache_key_by_slug(), product, timeout=600)
        warmed_count += 1
    
    logger.info(f"Warmed cache for {warmed_count} featured products")
    
    # Warm cache for categories
    categories = Category.objects.filter(is_active=True)[:10]
    for category in categories:
        cache.set(category.get_cache_key(), category, timeout=600)
        
        # Warm category products
        category_products = Product.objects.filter(
            category=category,
            status='published'
        ).select_related('category')[:10]
        
        cache.set(
            f'category_{category.id}_products',
            list(category_products),
            timeout=300
        )
    
    logger.info(f"Warmed cache for {len(categories)} categories")
    
    return {
        'products_warmed': warmed_count,
        'categories_warmed': len(categories)
    }


@shared_task(name='products.tasks.cleanup_expired_cache')
def cleanup_expired_cache():
    """
    Clean up expired cache entries.
    Runs every hour via Celery Beat.
    """
    logger.info("Starting cache cleanup task...")
    
    # Redis automatically handles TTL, but we can log statistics
    stats = get_cache_statistics()
    
    logger.info(f"Cache statistics: {stats}")
    
    return stats


@shared_task(name='products.tasks.generate_cache_statistics')
def generate_cache_statistics():
    """
    Generate and cache product statistics.
    Runs every 15 minutes via Celery Beat.
    """
    logger.info("Generating product statistics...")
    
    from django.db import models
    
    stats = {
        'total_products': Product.objects.count(),
        'published_products': Product.objects.filter(status='published').count(),
        'draft_products': Product.objects.filter(status='draft').count(),
        'archived_products': Product.objects.filter(status='archived').count(),
        'total_stock': Product.objects.aggregate(total=Sum('stock_quantity'))['total'] or 0,
        'low_stock_products': Product.objects.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=models.F('low_stock_threshold')
        ).count(),
        'out_of_stock_products': Product.objects.filter(stock_quantity=0).count(),
        'featured_products': Product.objects.filter(is_featured=True).count(),
        'average_price': float(Product.objects.aggregate(avg=Avg('price'))['avg'] or 0),
        'total_value': float(Product.objects.aggregate(
            total=Sum(models.F('price') * models.F('stock_quantity'))
        )['total'] or 0),
    }
    
    # Cache for 15 minutes
    cache.set('product_statistics', stats, timeout=900)
    
    logger.info(f"Generated statistics: {stats}")
    
    return stats


@shared_task(name='products.tasks.process_bulk_import')
def process_bulk_import(products_data):
    """
    Process bulk product import asynchronously.
    Demonstrates async data processing with cache invalidation.
    
    Args:
        products_data: List of product dictionaries
    """
    logger.info(f"Processing bulk import of {len(products_data)} products...")
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    for product_data in products_data:
        try:
            sku = product_data.get('sku')
            
            # Check if product exists
            product, created = Product.objects.update_or_create(
                sku=sku,
                defaults=product_data
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
        except Exception as e:
            logger.error(f"Error importing product {product_data.get('sku')}: {e}")
            error_count += 1
    
    # Invalidate all product list caches after bulk operation
    clear_all_product_caches()
    
    result = {
        'created': created_count,
        'updated': updated_count,
        'errors': error_count,
        'total': len(products_data)
    }
    
    logger.info(f"Bulk import completed: {result}")
    
    return result


@shared_task(name='products.tasks.update_product_prices')
def update_product_prices(price_updates):
    """
    Update product prices asynchronously.
    
    Args:
        price_updates: Dictionary of {product_id: new_price}
    """
    logger.info(f"Updating prices for {len(price_updates)} products...")
    
    updated_count = 0
    
    for product_id, new_price in price_updates.items():
        try:
            product = Product.objects.get(id=product_id)
            product.price = new_price
            product.save()
            updated_count += 1
        except Product.DoesNotExist:
            logger.error(f"Product {product_id} not found")
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
    
    logger.info(f"Updated {updated_count} product prices")
    
    return {'updated': updated_count}


@shared_task(name='products.tasks.sync_inventory')
def sync_inventory(inventory_data):
    """
    Sync inventory from external system asynchronously.
    
    Args:
        inventory_data: Dictionary of {sku: stock_quantity}
    """
    logger.info(f"Syncing inventory for {len(inventory_data)} products...")
    
    updated_count = 0
    
    for sku, quantity in inventory_data.items():
        try:
            product = Product.objects.get(sku=sku)
            product.stock_quantity = quantity
            product.save()
            updated_count += 1
        except Product.DoesNotExist:
            logger.error(f"Product with SKU {sku} not found")
        except Exception as e:
            logger.error(f"Error syncing inventory for {sku}: {e}")
    
    logger.info(f"Synced inventory for {updated_count} products")
    
    return {'updated': updated_count}


@shared_task(name='products.tasks.generate_sitemap_cache')
def generate_sitemap_cache():
    """
    Generate and cache sitemap data for all published products.
    Useful for SEO and quick sitemap generation.
    """
    logger.info("Generating sitemap cache...")
    
    products = Product.objects.filter(status='published').values(
        'slug', 'updated_at'
    )
    
    sitemap_data = list(products)
    
    # Cache for 1 hour
    cache.set('sitemap_products', sitemap_data, timeout=3600)
    
    logger.info(f"Cached sitemap for {len(sitemap_data)} products")
    
    return {'products': len(sitemap_data)}


@shared_task(name='products.tasks.analyze_cache_performance')
def analyze_cache_performance():
    """
    Analyze cache performance and log insights.
    Helps identify optimization opportunities.
    """
    logger.info("Analyzing cache performance...")
    
    stats = get_cache_statistics()
    
    # Calculate recommendations
    recommendations = []
    
    if stats['hit_rate'] < 70:
        recommendations.append("Low cache hit rate - consider increasing TTL values")
    
    if stats['total_keys'] > 10000:
        recommendations.append("High number of cached keys - consider cache key optimization")
    
    analysis = {
        'statistics': stats,
        'recommendations': recommendations,
        'timestamp': cache.get('cache_analysis_timestamp')
    }
    
    # Cache analysis results
    import datetime
    analysis['timestamp'] = datetime.datetime.now().isoformat()
    cache.set('cache_analysis', analysis, timeout=900)  # 15 minutes
    
    logger.info(f"Cache analysis: {analysis}")
    
    return analysis


@shared_task(bind=True, name='products.tasks.long_running_report')
def long_running_report(self, report_type):
    """
    Generate long-running reports asynchronously.
    Demonstrates task progress tracking.
    
    Args:
        report_type: Type of report to generate
    """
    logger.info(f"Starting {report_type} report generation...")
    
    total_steps = 100
    
    for i in range(total_steps):
        # Simulate work
        import time
        time.sleep(0.1)
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': total_steps}
        )
    
    result = {
        'report_type': report_type,
        'status': 'completed',
        'total_products': Product.objects.count()
    }
    
    logger.info(f"Report {report_type} completed: {result}")
    
    return result