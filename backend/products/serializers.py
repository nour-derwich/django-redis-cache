"""
Product serializers with caching strategies.
"""
from rest_framework import serializers
from .models.prodect import Product
from .models.category import Category
from django.core.cache import cache


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description',
            'is_active', 'product_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_product_count(self, obj):
        """Get product count with caching."""
        cache_key = f'category_{obj.id}_product_count'
        count = cache.get(cache_key)
        
        if count is None:
            count = obj.products.filter(status='published').count()
            cache.set(cache_key, count, timeout=300)  # 5 minutes
        
        return count


class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for product lists.
    Optimized for performance with minimal fields.
    """
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku',
            'short_description', 'category_name',
            'price', 'compare_at_price',
            'is_on_sale', 'discount_percentage',
            'stock_quantity', 'is_in_stock',
            'status', 'is_featured',
            'image', 'thumbnail',
            'created_at'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual product views.
    Includes all fields and related data.
    """
    
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku',
            'description', 'short_description',
            'category', 'category_id',
            'price', 'compare_at_price', 'cost',
            'is_on_sale', 'discount_percentage',
            'stock_quantity', 'low_stock_threshold',
            'is_in_stock', 'is_low_stock',
            'status', 'is_featured',
            'image', 'thumbnail',
            'meta_title', 'meta_description',
            'view_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'view_count']
    
    def validate_sku(self, value):
        """Validate SKU uniqueness."""
        instance = self.instance
        if Product.objects.exclude(pk=instance.pk if instance else None).filter(sku=value).exists():
            raise serializers.ValidationError("Product with this SKU already exists.")
        return value
    
    def validate_slug(self, value):
        """Validate slug uniqueness."""
        instance = self.instance
        if Product.objects.exclude(pk=instance.pk if instance else None).filter(slug=value).exists():
            raise serializers.ValidationError("Product with this slug already exists.")
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        price = data.get('price', self.instance.price if self.instance else None)
        compare_at_price = data.get('compare_at_price', 
                                     self.instance.compare_at_price if self.instance else None)
        
        if compare_at_price and price and compare_at_price <= price:
            raise serializers.ValidationError({
                'compare_at_price': 'Compare at price must be greater than the regular price.'
            })
        
        return data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating products.
    Includes validation and automatic cache invalidation.
    """
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'sku',
            'description', 'short_description',
            'category',
            'price', 'compare_at_price', 'cost',
            'stock_quantity', 'low_stock_threshold',
            'status', 'is_featured',
            'image', 'thumbnail',
            'meta_title', 'meta_description'
        ]
    
    def create(self, validated_data):
        """Create product and invalidate cache."""
        product = super().create(validated_data)
        # Cache is automatically invalidated via signals
        return product
    
    def update(self, instance, validated_data):
        """Update product and invalidate cache."""
        product = super().update(instance, validated_data)
        # Cache is automatically invalidated via signals
        return product


class ProductStatisticsSerializer(serializers.Serializer):
    """Serializer for product statistics."""
    
    total_products = serializers.IntegerField()
    published_products = serializers.IntegerField()
    draft_products = serializers.IntegerField()
    archived_products = serializers.IntegerField()
    total_stock = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    featured_products = serializers.IntegerField()
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)