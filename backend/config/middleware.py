"""
middleware.py — custom middleware for the Redis caching demo.

Three middlewares included:

1. CacheMonitorMiddleware
   Tracks cache hits / misses per request.
   Adds X-Cache-Hit and X-Cache-Response-Time headers so the React
   frontend (and curl) can see whether Redis served the response.

2. CacheBypassMiddleware
   Lets staff users append ?nocache=1 to skip the cache during debugging.

3. RedisCacheHeaderMiddleware
   Adds cache-control headers that match the TTL stored in Redis,
   so browsers and CDNs cache responses for the right amount of time.
"""
import time
import logging

from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 1. CacheMonitorMiddleware
# ──────────────────────────────────────────────────────────────────────────────

class CacheMonitorMiddleware(MiddlewareMixin):
    """
    Attaches three response headers to every API request:

        X-Cache-Hit          : "true" | "false"
        X-Cache-Response-Time: elapsed milliseconds as a string  e.g. "4.32"
        X-Cache-Key          : the cache key that was checked     (debug info)

    How it works
    ────────────
    process_request  → record start time + derive the cache key Django would use
    process_response → measure elapsed time, check whether key exists in Redis,
                       stamp the three headers, return the response

    The cache key logic mirrors what Django's cache_page decorator produces,
    so the "X-Cache-Hit: true" header is accurate for view-level caching.
    """

    MONITORED_PATHS = ("/api/",)          # only watch API endpoints

    def process_request(self, request):
        request._cache_monitor_start = time.monotonic()
        request._cache_monitor_key = self._derive_cache_key(request)

    def process_response(self, request, response):
        # Only instrument API paths
        if not any(request.path.startswith(p) for p in self.MONITORED_PATHS):
            return response

        start = getattr(request, "_cache_monitor_start", None)
        if start is None:
            return response

        # Elapsed time in ms, rounded to 2 decimal places
        elapsed_ms = round((time.monotonic() - start) * 1000, 2)

        # Did Redis actually have this key?
        cache_key = getattr(request, "_cache_monitor_key", "")
        cache_hit = cache.get(cache_key) is not None if cache_key else False

        # Stamp headers — lowercase names are preferred for HTTP/2
        response["X-Cache-Hit"] = "true" if cache_hit else "false"
        response["X-Cache-Response-Time"] = str(elapsed_ms)
        response["X-Cache-Key"] = cache_key or "n/a"

        # Expose the custom headers to cross-origin (React) clients
        existing = response.get("Access-Control-Expose-Headers", "")
        extra = "X-Cache-Hit, X-Cache-Response-Time, X-Cache-Key"
        response["Access-Control-Expose-Headers"] = (
            f"{existing}, {extra}" if existing else extra
        )

        logger.debug(
            "Cache monitor | %s %s | hit=%s | %.2fms",
            request.method,
            request.path,
            cache_hit,
            elapsed_ms,
        )

        return response

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _derive_cache_key(request) -> str:
        """
        Reproduce the cache key that ProductViewSet.list() generates.
        Returns "" for paths we don't track.
        """
        if request.path == "/api/products/" and request.method == "GET":
            params = request.GET.dict()
            return f"products_list_{hash(frozenset(params.items()))}"

        # /api/products/{id}/  → individual product cache key
        parts = [p for p in request.path.split("/") if p]   # drop empty strings
        if (
            len(parts) == 3
            and parts[0] == "api"
            and parts[1] == "products"
            and parts[2].isdigit()
            and request.method == "GET"
        ):
            return f"product_{parts[2]}"

        return ""


# ──────────────────────────────────────────────────────────────────────────────
# 2. CacheBypassMiddleware
# ──────────────────────────────────────────────────────────────────────────────

class CacheBypassMiddleware(MiddlewareMixin):
    """
    Lets staff users append ``?nocache=1`` to any request to bypass Redis.

    When ``nocache=1`` is present:
      • The cache key for that request is deleted before the view runs.
      • The response gets ``Cache-Control: no-store`` so it is never cached.

    Usage
    ─────
        GET /api/products/?nocache=1          ← forces DB hit
        GET /api/products/42/?nocache=1       ← forces DB hit for product 42

    ⚠  Only staff users can bypass the cache.  Regular users are ignored.
    """

    def process_request(self, request):
        if not self._should_bypass(request):
            return None

        cache_key = CacheMonitorMiddleware._derive_cache_key(request)
        if cache_key:
            cache.delete(cache_key)
            logger.info("Cache bypass | deleted key '%s' for %s", cache_key, request.user)

        # Flag so process_response can add the header
        request._cache_bypassed = True

    def process_response(self, request, response):
        if getattr(request, "_cache_bypassed", False):
            response["Cache-Control"] = "no-store"
            response["X-Cache-Bypassed"] = "true"
        return response

    @staticmethod
    def _should_bypass(request) -> bool:
        return (
            request.GET.get("nocache") == "1"
            and hasattr(request, "user")
            and request.user.is_authenticated
            and request.user.is_staff
        )


# ──────────────────────────────────────────────────────────────────────────────
# 3. RedisCacheHeaderMiddleware
# ──────────────────────────────────────────────────────────────────────────────

class RedisCacheHeaderMiddleware(MiddlewareMixin):
    """
    Adds ``Cache-Control`` and ``Vary`` headers that match your Redis TTLs.

    Rules applied (in order, first match wins):

        Path                         Cache-Control
        ─────────────────────────────────────────
        /api/products/{id}/          public, max-age=300   (5 min  — object cache)
        /api/products/               public, max-age=60    (1 min  — list cache)
        /api/products/statistics/    public, max-age=600   (10 min — stats cache)
        /api/products/featured/      public, max-age=300   (5 min)
        /api/categories/             public, max-age=300   (5 min)
        POST / PUT / PATCH / DELETE  no-store              (mutations never cached)
        Everything else              no-cache              (re-validate each time)

    Also adds ``Vary: Cookie, Authorization`` so caches differentiate between
    authenticated and anonymous responses.
    """

    RULES = [
        # (path_prefix, method, max_age)
        ("/api/products/statistics/", "GET", 600),
        ("/api/products/featured/",   "GET", 300),
        ("/api/categories/",          "GET", 300),
        ("/api/products/",            "GET", 60),   # list endpoint (less specific)
    ]

    DETAIL_MAX_AGE = 300    # /api/products/{id}/
    MUTATION_DIRECTIVE = "no-store"
    DEFAULT_DIRECTIVE = "no-cache"

    def process_response(self, request, response):
        method = request.method.upper()

        # Never cache mutations
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            response["Cache-Control"] = self.MUTATION_DIRECTIVE
            return response

        # Add Vary header so caches separate auth'd from anon responses
        response["Vary"] = "Cookie, Authorization"

        # Match specific rules first
        for path_prefix, rule_method, max_age in self.RULES:
            if request.path.startswith(path_prefix) and method == rule_method:
                response["Cache-Control"] = f"public, max-age={max_age}"
                return response

        # Individual product detail: /api/products/42/
        if self._is_product_detail(request.path) and method == "GET":
            response["Cache-Control"] = f"public, max-age={self.DETAIL_MAX_AGE}"
            return response

        # Fallback
        response["Cache-Control"] = self.DEFAULT_DIRECTIVE
        return response

    @staticmethod
    def _is_product_detail(path: str) -> bool:
        """
        Return True for /api/products/42/ style paths.

        Split examples:
          "/api/products/42/"   → ['', 'api', 'products', '42']  ← last is digit
          "/api/products/"      → ['', 'api', 'products', '']    ← last is empty
          "/api/products/featured/" → last is 'featured'         ← NOT a digit
        """
        parts = [p for p in path.split("/") if p]   # drop empty strings
        # Must have exactly 3 segments: api / products / <id>
        return (
            len(parts) == 3
            and parts[0] == "api"
            and parts[1] == "products"
            and parts[2].isdigit()
        )