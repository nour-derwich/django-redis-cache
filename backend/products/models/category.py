from django.db import models
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ..signals import  invalidate_category_cache_on_save, invalidate_category_cache_on_delete
class Category(models.Model):
    """Product category model."""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_cache_key(self):
        """Generate cache key for this category."""
        return f'category_{self.id}'
    
    def invalidate_cache(self):
        """Invalidate all caches related to this category."""
        cache.delete(self.get_cache_key())
        cache.delete('categories_list')
        cache.delete(f'category_slug_{self.slug}')
        # Invalidate products in this category
        cache.delete(f'category_{self.id}_products')