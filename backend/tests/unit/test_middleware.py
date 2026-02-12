"""
Middleware tests — CacheMonitorMiddleware, CacheBypassMiddleware,
RedisCacheHeaderMiddleware.
"""
import pytest
from django.core.cache import cache
from django.test import RequestFactory, override_settings
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from products.middleware import (
    CacheMonitorMiddleware,
    CacheBypassMiddleware,
    RedisCacheHeaderMiddleware,
)

User = get_user_model()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _mock_response(content=b"ok", status=200):
    return HttpResponse(content, status=status)


def _get_request(factory, path, params=None, user=None):
    request = factory.get(path, params or {})
    if user:
        request.user = user
    return request


# ══════════════════════════════════════════════════════
# CacheMonitorMiddleware
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCacheMonitorMiddleware:

    @pytest.fixture
    def mw(self):
        return CacheMonitorMiddleware(get_response=lambda r: _mock_response())

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    def test_adds_cache_hit_false_when_cache_empty(self, mw, factory):
        request = factory.get("/api/products/")
        mw.process_request(request)
        response = _mock_response()
        response = mw.process_response(request, response)

        assert response["X-Cache-Hit"] == "false"

    def test_adds_cache_hit_true_when_key_exists(self, mw, factory):
        request = factory.get("/api/products/")
        mw.process_request(request)

        # Pre-fill the cache with the key the middleware will check
        key = CacheMonitorMiddleware._derive_cache_key(request)
        cache.set(key, {"results": []}, 60)

        response = _mock_response()
        response = mw.process_response(request, response)

        assert response["X-Cache-Hit"] == "true"

    def test_adds_response_time_header(self, mw, factory):
        request = factory.get("/api/products/")
        mw.process_request(request)
        response = mw.process_response(request, _mock_response())

        assert "X-Cache-Response-Time" in response
        elapsed = float(response["X-Cache-Response-Time"])
        assert elapsed >= 0

    def test_skips_non_api_paths(self, mw, factory):
        request = factory.get("/admin/")
        mw.process_request(request)
        response = mw.process_response(request, _mock_response())

        assert "X-Cache-Hit" not in response

    def test_exposes_headers_for_cors(self, mw, factory):
        request = factory.get("/api/products/")
        mw.process_request(request)
        response = mw.process_response(request, _mock_response())

        expose = response.get("Access-Control-Expose-Headers", "")
        assert "X-Cache-Hit" in expose
        assert "X-Cache-Response-Time" in expose

    def test_derive_cache_key_product_list(self, factory):
        request = factory.get("/api/products/")
        key = CacheMonitorMiddleware._derive_cache_key(request)
        assert key.startswith("products_list_")

    def test_derive_cache_key_product_detail(self, factory):
        request = factory.get("/api/products/42/")
        key = CacheMonitorMiddleware._derive_cache_key(request)
        assert key == "product_42"

    def test_derive_cache_key_unknown_path_returns_empty(self, factory):
        request = factory.get("/api/categories/")
        key = CacheMonitorMiddleware._derive_cache_key(request)
        assert key == ""


# ══════════════════════════════════════════════════════
# CacheBypassMiddleware
# ══════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCacheBypassMiddleware:

    @pytest.fixture
    def mw(self):
        return CacheBypassMiddleware(get_response=lambda r: _mock_response())

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    def test_non_staff_cannot_bypass(self, mw, factory, regular_user):
        request = factory.get("/api/products/", {"nocache": "1"})
        request.user = regular_user

        mw.process_request(request)
        assert not getattr(request, "_cache_bypassed", False)

    def test_staff_can_bypass(self, mw, factory, admin_user):
        # Pre-fill cache
        cache.set("products_list_0", "stale", 60)

        request = factory.get("/api/products/", {"nocache": "1"})
        request.user = admin_user

        mw.process_request(request)
        assert getattr(request, "_cache_bypassed", False)

    def test_bypass_adds_no_store_header(self, mw, factory, admin_user):
        request = factory.get("/api/products/", {"nocache": "1"})
        request.user = admin_user

        mw.process_request(request)
        response = mw.process_response(request, _mock_response())

        assert response["Cache-Control"] == "no-store"
        assert response["X-Cache-Bypassed"] == "true"

    def test_normal_request_no_bypass_header(self, mw, factory):
        request = factory.get("/api/products/")
        # No user attribute needed — anon request
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

        mw.process_request(request)
        response = mw.process_response(request, _mock_response())

        assert "X-Cache-Bypassed" not in response

    def test_without_nocache_param_staff_not_bypassed(self, mw, factory, admin_user):
        request = factory.get("/api/products/")   # no ?nocache=1
        request.user = admin_user

        mw.process_request(request)
        assert not getattr(request, "_cache_bypassed", False)


# ══════════════════════════════════════════════════════
# RedisCacheHeaderMiddleware
# ══════════════════════════════════════════════════════

class TestRedisCacheHeaderMiddleware:

    @pytest.fixture
    def mw(self):
        return RedisCacheHeaderMiddleware(get_response=lambda r: _mock_response())

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    def test_product_list_gets_60s_max_age(self, mw, factory):
        request = factory.get("/api/products/")
        response = mw.process_response(request, _mock_response())
        assert "max-age=60" in response["Cache-Control"]

    def test_product_detail_gets_300s_max_age(self, mw, factory):
        request = factory.get("/api/products/42/")
        response = mw.process_response(request, _mock_response())
        assert "max-age=300" in response["Cache-Control"]

    def test_statistics_gets_600s_max_age(self, mw, factory):
        request = factory.get("/api/products/statistics/")
        response = mw.process_response(request, _mock_response())
        assert "max-age=600" in response["Cache-Control"]

    def test_featured_gets_300s_max_age(self, mw, factory):
        request = factory.get("/api/products/featured/")
        response = mw.process_response(request, _mock_response())
        assert "max-age=300" in response["Cache-Control"]

    def test_categories_get_300s_max_age(self, mw, factory):
        request = factory.get("/api/categories/")
        response = mw.process_response(request, _mock_response())
        assert "max-age=300" in response["Cache-Control"]

    def test_post_gets_no_store(self, mw, factory):
        request = factory.post("/api/products/")
        response = mw.process_response(request, _mock_response())
        assert response["Cache-Control"] == "no-store"

    def test_delete_gets_no_store(self, mw, factory):
        request = factory.delete("/api/products/42/")
        response = mw.process_response(request, _mock_response())
        assert response["Cache-Control"] == "no-store"

    def test_patch_gets_no_store(self, mw, factory):
        request = factory.patch("/api/products/42/")
        response = mw.process_response(request, _mock_response())
        assert response["Cache-Control"] == "no-store"

    def test_vary_header_on_get(self, mw, factory):
        request = factory.get("/api/products/")
        response = mw.process_response(request, _mock_response())
        assert "Cookie" in response["Vary"]
        assert "Authorization" in response["Vary"]

    def test_unknown_path_gets_no_cache(self, mw, factory):
        request = factory.get("/api/some-unknown-endpoint/")
        response = mw.process_response(request, _mock_response())
        assert response["Cache-Control"] == "no-cache"

    def test_is_product_detail_true(self):
        assert RedisCacheHeaderMiddleware._is_product_detail("/api/products/42/") is True

    def test_is_product_detail_false_for_list(self):
        assert RedisCacheHeaderMiddleware._is_product_detail("/api/products/") is False

    def test_is_product_detail_false_for_action(self):
        assert RedisCacheHeaderMiddleware._is_product_detail("/api/products/featured/") is False