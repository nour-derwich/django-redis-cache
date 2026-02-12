"""
Product views with advanced Redis caching patterns.
Demonstrates multiple caching strategies.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache, caches
from django.db.models import Sum, Avg, Count, Q , F
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django_filters.rest_framework import DjangoFilterBackend

from .models .category import Category
from .models.product import Product
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductStatisticsSerializer,
    CategorySerializer
)
from .cache_utils import (
    get_cached_product,
    get_cached_products_list,
    get_cached_category,
    invalidate_product_list_cache
)
import logging

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD with advanced caching strategies.
    
    Caching Patterns Demonstrated:
    1. View-level caching with @cache_page decorator
    2. Manual low-level cache operations
    3. QuerySet caching
    4. API response caching
    5. Selective cache invalidation
    """
    
    queryset = Product.objects.select_related('category').all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'category', 'is_featured']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['created_at', 'price', 'name', 'stock_quantity']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        """
        Optimized queryset with select_related for better performance.
        Cache the queryset at database level.
        """
        queryset = super().get_queryset()
        
        # Only show published products to non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')
        
        return queryset
    
    @method_decorator(cache_page(60))  # Cache for 1 minute
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        """
        List products with automatic caching.
        Cache key varies by query parameters and user authentication.
        """
        # Build cache key based on query params
        query_params = request.query_params.dict()
        cache_key = f"products_list_{hash(frozenset(query_params.items()))}"
        
        # Try to get from cache
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info(f"Cache HIT for products list: {cache_key}")
            return Response(cached_response)
        
        logger.info(f"Cache MISS for products list: {cache_key}")
        
        # If not in cache, perform query
        response = super().list(request, *args, **kwargs)
        
        # Cache the response data
        cache.set(cache_key, response.data, timeout=60)
        
        return response
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve single product with caching.
        Uses low-level cache API for fine-grained control.
        """
        product_id = kwargs.get('pk')
        
        # Try to get from cache
        cached_product = get_cached_product(product_id)
        
        if cached_product:
            logger.info(f"Cache HIT for product: {product_id}")
            serializer = self.get_serializer(cached_product)
            
            # Increment view count asynchronously (doesn't invalidate cache)
            cached_product.increment_view_count()
            
            return Response(serializer.data)
        
        logger.info(f"Cache MISS for product: {product_id}")
        
        # Get from database and cache it
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Cache the product object
        cache.set(instance.get_cache_key(), instance, timeout=300)
        
        # Increment view count
        instance.increment_view_count()
        
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create product and invalidate list cache."""
        response = super().create(request, *args, **kwargs)
        
        # Invalidate list caches
        invalidate_product_list_cache()
        
        logger.info(f"Product created: {response.data.get('id')}")
        return response
    
    def update(self, request, *args, **kwargs):
        """Update product and invalidate related caches."""
        response = super().update(request, *args, **kwargs)
        
        # Cache invalidation is handled by signals
        logger.info(f"Product updated: {kwargs.get('pk')}")
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Delete product and invalidate caches."""
        product_id = kwargs.get('pk')
        response = super().destroy(request, *args, **kwargs)
        
        logger.info(f"Product deleted: {product_id}")
        return response
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured products with dedicated cache.
        Cached separately from main product list.
        """
        cache_key = 'products_featured'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Cache HIT for featured products")
            return Response(cached_data)
        
        logger.info(f"Cache MISS for featured products")
        
        queryset = self.get_queryset().filter(is_featured=True, status='published')[:10]
        serializer = ProductListSerializer(queryset, many=True)
        
        # Cache for 5 minutes
        cache.set(cache_key, serializer.data, timeout=300)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get product statistics with caching.
        Demonstrates caching of aggregated queries.
        """
        cache_key = 'product_statistics'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            logger.info("Cache HIT for product statistics")
            return Response(cached_stats)
        
        logger.info("Cache MISS for product statistics")
        
        # Perform expensive aggregation queries
        stats = {
            'total_products': Product.objects.count(),
            'published_products': Product.objects.filter(status='published').count(),
            'draft_products': Product.objects.filter(status='draft').count(),
            'archived_products': Product.objects.filter(status='archived').count(),
            'total_stock': Product.objects.aggregate(total=Sum('stock_quantity'))['total'] or 0,
            'low_stock_products': Product.objects.filter(
                stock_quantity__gt=0,
                stock_quantity__lte=F('low_stock_threshold')
            ).count(),
            'out_of_stock_products': Product.objects.filter(stock_quantity=0).count(),
            'featured_products': Product.objects.filter(is_featured=True).count(),
            'average_price': Product.objects.aggregate(avg=Avg('price'))['avg'] or 0,
            'total_value': Product.objects.aggregate(
                total=Sum(F('price') * F('stock_quantity'))
            )['total'] or 0,
        }
        
        serializer = ProductStatisticsSerializer(stats)
        
        # Cache for 10 minutes
        cache.set(cache_key, serializer.data, timeout=600)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def clear_cache(self, request):
        """
        Admin endpoint to manually clear product caches.
        Useful for debugging and testing.
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Clear all product-related caches
        cache.delete_pattern('product_*')
        cache.delete_pattern('products_*')
        cache.delete_pattern('category_*')
        
        logger.info("All product caches cleared manually")
        
        return Response({'message': 'Cache cleared successfully'})
    
    @action(detail=False, methods=['get'])
    def cache_info(self, request):
        """
        Get cache statistics and information.
        Useful for monitoring cache performance.
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get Redis cache client
        redis_cache = caches['default']
        redis_client = redis_cache.client.get_client()
        
        info = {
            'redis_info': redis_client.info('stats'),
            'cache_keys': redis_client.keys('*'),
            'total_keys': redis_client.dbsize(),
        }
        
        return Response(info)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD with caching.
    """
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    def list(self, request, *args, **kwargs):
        """List categories with caching."""
        cache_key = 'categories_list'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        
        return response
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve category with caching."""
        slug = kwargs.get('slug')
        cache_key = f'category_slug_{slug}'
        
        cached_category = cache.get(cache_key)
        
        if cached_category:
            serializer = self.get_serializer(cached_category)
            return Response(serializer.data)
        
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        cache.set(cache_key, instance, timeout=300)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get products in a category with caching."""
        category = self.get_object()
        cache_key = f'category_{category.id}_products'
        
        cached_products = cache.get(cache_key)
        
        if cached_products:
            return Response(cached_products)
        
        products = Product.objects.filter(
            category=category,
            status='published'
        ).select_related('category')
        
        serializer = ProductListSerializer(products, many=True)
        cache.set(cache_key, serializer.data, timeout=300)
        
        return Response(serializer.data)
