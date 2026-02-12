"""
Admin configuration for products app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    
    list_display = ['name', 'slug', 'product_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def product_count(self, obj):
        """Display product count."""
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""
    
    list_display = [
        'name', 'sku', 'category', 'price_display',
        'stock_status', 'status', 'is_featured',
        'view_count', 'created_at'
    ]
    list_filter = ['status', 'is_featured', 'category', 'created_at']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'view_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'description', 'short_description')
        }),
        ('Categorization', {
            'fields': ('category',)
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'cost')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'low_stock_threshold')
        }),
        ('Status', {
            'fields': ('status', 'is_featured')
        }),
        ('Media', {
            'fields': ('image', 'thumbnail')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        """Display price with sale indicator."""
        if obj.is_on_sale:
            return format_html(
                '<span style="color: red;">${} <s>${}</s></span>',
                obj.price,
                obj.compare_at_price
            )
        return f'${obj.price}'
    price_display.short_description = 'Price'
    
    def stock_status(self, obj):
        """Display stock status with color coding."""
        if obj.stock_quantity == 0:
            color = 'red'
            text = 'Out of Stock'
        elif obj.is_low_stock:
            color = 'orange'
            text = f'Low Stock ({obj.stock_quantity})'
        else:
            color = 'green'
            text = f'In Stock ({obj.stock_quantity})'
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            text
        )
    stock_status.short_description = 'Stock'
    
    actions = ['make_published', 'make_draft', 'make_featured', 'clear_cache']
    
    def make_published(self, request, queryset):
        """Bulk action to publish products."""
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} products were published.')
    make_published.short_description = 'Publish selected products'
    
    def make_draft(self, request, queryset):
        """Bulk action to set products as draft."""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} products were set to draft.')
    make_draft.short_description = 'Set selected products as draft'
    
    def make_featured(self, request, queryset):
        """Bulk action to feature products."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} products were marked as featured.')
    make_featured.short_description = 'Mark selected products as featured'
    
    def clear_cache(self, request, queryset):
        """Bulk action to clear cache for selected products."""
        from .cache_utils import clear_all_product_caches
        clear_all_product_caches()
        self.message_user(request, 'Cache cleared for all products.')
    clear_cache.short_description = 'Clear cache for selected products'