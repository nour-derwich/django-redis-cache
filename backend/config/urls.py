"""
URL configuration for Redis Caching Demo project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # JWT Auth — csrf_exempt because JWT is stateless (no session cookie needed)
    path('api/auth/login/',   csrf_exempt(TokenObtainPairView.as_view()),  name='token_obtain_pair'),
    path('api/auth/refresh/', csrf_exempt(TokenRefreshView.as_view()),     name='token_refresh'),
    path('api/auth/verify/',  csrf_exempt(TokenVerifyView.as_view()),      name='token_verify'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(),                      name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),

    # API Endpoints
    path('api/', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)