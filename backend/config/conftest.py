"""
Pytest configuration for Django Redis Caching Demo.
"""
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    """Provide API client for testing."""
    return APIClient()


@pytest.fixture
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup test database."""
    with django_db_blocker.unblock():
        # Additional setup if needed
        pass