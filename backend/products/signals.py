"""
Cache invalidation signals for products app.
Automatically invalidates cache when models are saved or deleted.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='products.Product')  # Use string reference to avoid circular import
def invalidate_product_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalidate product cache when a product is created or updated.
    This ensures cache stays fresh.
    """
    action = "created" if created else "updated"
    logger.info(f"Product {instance.id} {action} - invalidating cache")
    instance.invalidate_cache()


@receiver(post_delete, sender='products.Product')
def invalidate_product_cache_on_delete(sender, instance, **kwargs):
    """Invalidate product cache when a product is deleted."""
    logger.info(f"Product {instance.id} deleted - invalidating cache")
    instance.invalidate_cache()


@receiver(post_save, sender='products.Category')
def invalidate_category_cache_on_save(sender, instance, **kwargs):
    """Invalidate category cache when a category is created or updated."""
    created = kwargs.get('created', False)
    action = "created" if created else "updated"
    logger.info(f"Category {instance.id} {action} - invalidating cache")
    instance.invalidate_cache()


@receiver(post_delete, sender='products.Category')
def invalidate_category_cache_on_delete(sender, instance, **kwargs):
    """Invalidate category cache when a category is deleted."""
    logger.info(f"Category {instance.id} deleted - invalidating cache")
    instance.invalidate_cache()