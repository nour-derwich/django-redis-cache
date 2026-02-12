from django.db import models
from django.core.cache import cache
from .category import Category

class Product(models.Model):
    """
    Product model with advanced caching patterns.
    Demonstrates cache invalidation on CRUD operations.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price for showing discounts"
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost price for internal use"
    )
    
    # Inventory
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    is_featured = models.BooleanField(default=False, db_index=True)
    
    # Images
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='products/thumbnails/', null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['-is_featured', '-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_on_sale(self):
        """Check if product is on sale."""
        return self.compare_at_price and self.compare_at_price > self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage."""
        if self.is_on_sale:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if product has low stock."""
        return 0 < self.stock_quantity <= self.low_stock_threshold
    
    def get_cache_key(self):
        """Generate cache key for this product."""
        return f'product_{self.id}'
    
    def get_cache_key_by_slug(self):
        """Generate cache key for slug lookup."""
        return f'product_slug_{self.slug}'
    
    def invalidate_cache(self):
        """
        Invalidate all caches related to this product.
        This is called automatically via signals.
        """
        # Delete individual product cache
        cache.delete(self.get_cache_key())
        cache.delete(self.get_cache_key_by_slug())
        
        # Delete list caches
        cache.delete('products_list')
        cache.delete('products_published')
        cache.delete('products_featured')
        
        # Delete category-specific caches
        if self.category:
            cache.delete(f'category_{self.category.id}_products')
        
        # Delete paginated caches (first 10 pages)
        for page in range(1, 11):
            cache.delete(f'products_page_{page}')
        
        # Delete statistics cache
        cache.delete('product_statistics')
    
    def increment_view_count(self):
        """Increment view count without triggering cache invalidation."""
        Product.objects.filter(id=self.id).update(view_count=models.F('view_count') + 1)


