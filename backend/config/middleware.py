# """
# config/middleware.py — custom middleware for the Redis caching demo.
# """
# import time
# import logging

# from django.http import HttpResponseBase
# from django.core.cache import cache
# from django.utils.deprecation import MiddlewareMixin

# logger = logging.getLogger(__name__)


# def is_real_response(response) -> bool:
#     """
#     Guard against Django passing a function instead of HttpResponse.
#     """
#     return isinstance(response, HttpResponseBase)


# class CacheMonitorMiddleware(MiddlewareMixin):
#     MONITORED_PATHS = ("/api/",)

#     def process_request(self, request):
#         request._cache_monitor_start = time.monotonic()
#         request._cache_monitor_key = self._derive_cache_key(request)

#     def process_response(self, request, response):
#         if not is_real_response(response):
#             return response
            
#         if not any(request.path.startswith(p) for p in self.MONITORED_PATHS):
#             return response

#         start = getattr(request, "_cache_monitor_start", None)
#         if start is None:
#             return response

#         elapsed_ms = round((time.monotonic() - start) * 1000, 2)
#         cache_key = getattr(request, "_cache_monitor_key", "")
#         cache_hit = cache.get(cache_key) is not None if cache_key else False

#         response["X-Cache-Hit"] = "true" if cache_hit else "false"
#         response["X-Cache-Response-Time"] = str(elapsed_ms)
#         response["X-Cache-Key"] = cache_key or "n/a"

#         existing = response.get("Access-Control-Expose-Headers", "")
#         extra = "X-Cache-Hit, X-Cache-Response-Time, X-Cache-Key"
#         response["Access-Control-Expose-Headers"] = (
#             f"{existing}, {extra}" if existing else extra
#         )
#         return response

#     @staticmethod
#     def _derive_cache_key(request) -> str:
#         if request.path == "/api/products/" and request.method == "GET":
#             params = request.GET.dict()
#             return f"products_list_{hash(frozenset(params.items()))}"
#         parts = [p for p in request.path.split("/") if p]
#         if (
#             len(parts) == 3
#             and parts[0] == "api"
#             and parts[1] == "products"
#             and parts[2].isdigit()
#             and request.method == "GET"
#         ):
#             return f"product_{parts[2]}"
#         return ""


# class CacheBypassMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         if not self._should_bypass(request):
#             return None
#         cache_key = CacheMonitorMiddleware._derive_cache_key(request)
#         if cache_key:
#             cache.delete(cache_key)
#         request._cache_bypassed = True

#     def process_response(self, request, response):
#         if not is_real_response(response):
#             return response
            
#         if getattr(request, "_cache_bypassed", False):
#             response["Cache-Control"] = "no-store"
#             response["X-Cache-Bypassed"] = "true"
#         return response

#     @staticmethod
#     def _should_bypass(request) -> bool:
#         return (
#             request.GET.get("nocache") == "1"
#             and hasattr(request, "user")
#             and request.user.is_authenticated
#             and request.user.is_staff
#         )


# class RedisCacheHeaderMiddleware(MiddlewareMixin):
#     API_PREFIX = "/api/"

#     RULES = [
#         ("/api/products/statistics/", "GET", 600),
#         ("/api/products/featured/",   "GET", 300),
#         ("/api/categories/",          "GET", 300),
#         ("/api/products/",            "GET", 60),
#     ]

#     DETAIL_MAX_AGE = 300
#     MUTATION_DIRECTIVE = "no-store"
#     DEFAULT_DIRECTIVE = "no-cache"

#     def process_response(self, request, response):
#         if not is_real_response(response):
#             return response
            
#         if not request.path.startswith(self.API_PREFIX):
#             return response

#         method = request.method.upper()

#         if method in ("POST", "PUT", "PATCH", "DELETE"):
#             response["Cache-Control"] = self.MUTATION_DIRECTIVE
#             return response

#         response["Vary"] = "Cookie, Authorization"

#         for path_prefix, rule_method, max_age in self.RULES:
#             if request.path.startswith(path_prefix) and method == rule_method:
#                 response["Cache-Control"] = f"public, max-age={max_age}"
#                 return response

#         if self._is_product_detail(request.path) and method == "GET":
#             response["Cache-Control"] = f"public, max-age={self.DETAIL_MAX_AGE}"
#             return response

#         response["Cache-Control"] = self.DEFAULT_DIRECTIVE
#         return response

#     @staticmethod
#     def _is_product_detail(path: str) -> bool:
#         parts = [p for p in path.split("/") if p]
#         return (
#             len(parts) == 3
#             and parts[0] == "api"
#             and parts[1] == "products"
#             and parts[2].isdigit()
#         )


# class FunctionResponseFixerMiddleware(MiddlewareMixin):
#     """
#     Middleware that ensures any function objects in the response chain
#     are properly handled before they reach other middleware.
#     """
    
#     def process_response(self, request, response):
#         # If response is not a proper HttpResponse object, fix it
#         if not isinstance(response, HttpResponseBase):
#             logger.error(f"Non-HttpResponse object detected: {type(response)} for path {request.path}")
            
#             # If it's a function, try to call it
#             if callable(response):
#                 try:
#                     logger.info(f"Attempting to call function response: {response}")
#                     response = response(request)
#                 except Exception as e:
#                     logger.error(f"Failed to call response function: {e}")
#                     from django.http import HttpResponseServerError
#                     return HttpResponseServerError(f"Middleware chain error: {e}")
            
#             # If it's still not a proper response, return a fallback
#             if not isinstance(response, HttpResponseBase):
#                 from django.http import HttpResponse
#                 logger.warning(f"Returning fallback response for type: {type(response)}")
#                 return HttpResponse("Middleware chain fixed response", status=500)
        
#         return response
#     """
#     Middleware that ensures any function objects in the response chain
#     are properly handled before they reach other middleware.
#     """
    
#     def process_response(self, request, response):
#         # If response is not a proper HttpResponse object,
#         # return a minimal response to prevent errors in subsequent middleware
#         if not isinstance(response, HttpResponseBase):
#             # If it's a function, try to call it to get a real response
#             if callable(response):
#                 try:
#                     response = response(request)
#                 except Exception:
#                     # If calling fails, return a 500 error
#                     from django.http import HttpResponseServerError
#                     return HttpResponseServerError("Middleware chain error")
            
#             # If it's still not a proper response, return a fallback
#             if not isinstance(response, HttpResponseBase):
#                 from django.http import HttpResponse
#                 response = HttpResponse("Middleware chain fixed response")
        
#         return response