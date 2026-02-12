"""
Shared pytest fixtures for the entire test suite.
Located at config/conftest.py
"""

import pytest
from decimal import Decimal
from django.core.cache import cache
from products.models.product import Product  
from products.models.category import Category


# ─────────────────────────────────────────────────────────
# AUTO-USED FIXTURES (run before/after every test)
# ─────────────────────────────────────────────────────────
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def auth_client(regular_user):
    """Return an authenticated API client with regular user."""
    client = APIClient()
    client.force_authenticate(user=regular_user)
    return client


@pytest.fixture
def admin_client(admin_user):
    """Return an authenticated API client with admin user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def staff_client(admin_user):
    """Alias for admin_client - for staff-level access tests."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


# ─────────────────────────────────────────────────────────
# CATEGORY FIXTURES
# ─────────────────────────────────────────────────────────

@pytest.fixture
def category(db):
    """Create a basic category for testing."""
    return Category.objects.create(
        name="Electronics",
        slug="electronics",
        description="Electronic devices and gadgets",
        is_active=True
    )


@pytest.fixture
def inactive_category(db):
    """Create an inactive category for testing."""
    return Category.objects.create(
        name="Archived Category",
        slug="archived",
        description="This category is not active",
        is_active=False
    )


# ─────────────────────────────────────────────────────────
# PRODUCT FIXTURES
# ─────────────────────────────────────────────────────────

@pytest.fixture
def product(db, category):
    """Create a regular product (not on sale, in stock)."""
    return Product.objects.create(
        name="Test Laptop",
        slug="test-laptop",
        sku="TL-001",
        description="A test laptop for unit tests",
        short_description="Test laptop",
        category=category,
        price=Decimal("999.99"),
        compare_at_price=None,
        cost=Decimal("700.00"),
        stock_quantity=50,
        low_stock_threshold=10,
        status="published",  # Explicitly published
        is_featured=False,
        view_count=0
    )


@pytest.fixture
def sale_product(db, category):
    """Create a product that is ON SALE (compare_at_price > price)."""
    return Product.objects.create(
        name="Sale Laptop",
        slug="sale-laptop",
        sku="SL-001",
        description="A laptop on sale",
        short_description="On sale!",
        category=category,
        price=Decimal("79.99"),
        compare_at_price=Decimal("129.99"),
        cost=Decimal("50.00"),
        stock_quantity=25,
        low_stock_threshold=5,
        status="published",  # Explicitly published
        is_featured=True,
        view_count=100
    )


@pytest.fixture
def featured_product(db, category):
    """Create a featured product."""
    return Product.objects.create(
        name="Featured Smartphone",
        slug="featured-phone",
        sku="FP-001",
        description="A featured product",
        short_description="Featured!",
        category=category,
        price=Decimal("599.99"),
        compare_at_price=Decimal("699.99"),
        cost=Decimal("400.00"),
        stock_quantity=30,
        low_stock_threshold=5,
        status="published",  # Explicitly published
        is_featured=True,
        view_count=500
    )


@pytest.fixture
def out_of_stock_product(db, category):
    """Create a product with zero stock."""
    return Product.objects.create(
        name="Out of Stock Item",
        slug="out-of-stock",
        sku="OOS-001",
        description="This item is out of stock",
        short_description="Sold out",
        category=category,
        price=Decimal("49.99"),
        compare_at_price=Decimal("59.99"),
        cost=Decimal("30.00"),
        stock_quantity=0,
        low_stock_threshold=5,
        status="published",  # Explicitly published
        is_featured=False,
        view_count=50
    )


@pytest.fixture
def draft_product(db, category):
    """Create a draft product (not published)."""
    return Product.objects.create(
        name="Draft Product",
        slug="draft-product",
        sku="DP-001",
        description="This product is still in draft",
        short_description="Work in progress",
        category=category,
        price=Decimal("199.99"),
        compare_at_price=None,
        cost=Decimal("120.00"),
        stock_quantity=0,
        low_stock_threshold=5,
        status="draft",
        is_featured=False,
        view_count=0
    )


@pytest.fixture
def low_stock_product(db, category):
    """Create a product with low stock (below threshold)."""
    return Product.objects.create(
        name="Low Stock Item",
        slug="low-stock",
        sku="LS-001",
        description="Running out soon",
        short_description="Almost gone!",
        category=category,
        price=Decimal("29.99"),
        compare_at_price=Decimal("39.99"),
        cost=Decimal("18.00"),
        stock_quantity=3,
        low_stock_threshold=10,
        status="published",  # Explicitly published
        is_featured=False,
        view_count=75
    )


# ─────────────────────────────────────────────────────────
# BULK PRODUCT FIXTURES
# ─────────────────────────────────────────────────────────

@pytest.fixture
def product_list(db, category):
    """Create 10 published products for list testing."""
    products = []
    for i in range(1, 11):
        product = Product.objects.create(
            name=f"Test Product {i}",
            slug=f"test-product-{i}",
            sku=f"TP-{i:03d}",
            description=f"Description for product {i}",
            short_description=f"Short desc {i}",
            category=category,
            price=Decimal(f"{99.99 + i}"),
            compare_at_price=Decimal(f"{129.99 + i}") if i % 2 == 0 else None,
            cost=Decimal(f"{70.00 + i}"),
            stock_quantity=i * 5,
            low_stock_threshold=10,
            status="published",  # Explicitly published
            is_featured=True if i % 3 == 0 else False,
            view_count=i * 10
        )
        products.append(product)
    return products


@pytest.fixture
def mixed_status_product_list(db, category):
    """Create products with different statuses."""
    products = []
    
    # 5 published
    for i in range(1, 6):
        products.append(Product.objects.create(
            name=f"Published Product {i}",
            slug=f"published-{i}",
            sku=f"PUB-{i:03d}",
            category=category,
            price=Decimal("49.99"),
            stock_quantity=10,
            status="published",  # Explicitly published
        ))
    
    # 3 draft
    for i in range(1, 4):
        products.append(Product.objects.create(
            name=f"Draft Product {i}",
            slug=f"draft-{i}",
            sku=f"DRF-{i:03d}",
            category=category,
            price=Decimal("39.99"),
            stock_quantity=0,
            status="draft",
        ))
    
    # 2 archived
    for i in range(1, 3):
        products.append(Product.objects.create(
            name=f"Archived Product {i}",
            slug=f"archived-{i}",
            sku=f"ARC-{i:03d}",
            category=category,
            price=Decimal("29.99"),
            stock_quantity=0,
            status="archived",
        ))
    
    return products


# ─────────────────────────────────────────────────────────
# USER FIXTURES
# ─────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db, django_user_model):
    """Create an admin user."""
    return django_user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123"
    )


@pytest.fixture
def regular_user(db, django_user_model):
    """Create a regular user."""
    return django_user_model.objects.create_user(
        username="user",
        email="user@example.com",
        password="userpass123"
    )


# ─────────────────────────────────────────────────────────
# REGISTER CUSTOM MARKS
# ─────────────────────────────────────────────────────────

def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    config.addinivalue_line(
        "markers", "cache: tests that interact with Redis cache"
    )
    config.addinivalue_line(
        "markers", "slow: tests that are slower than usual"
    )