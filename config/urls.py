"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import HttpResponse, JsonResponse


def health_check(request):
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    path('', include('django_prometheus.urls')),
    path('health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('products/', include('main.urls')),
    path('', lambda request: HttpResponse("Welcome to the homepage")),
    
    # Third-party integrations
    path("api-auth/", include("rest_framework.urls")),
    # path("accounts/", include("allauth.urls")),
    path("api-download-schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api-documents/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]


# Serve media files only in development
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Admin branding
admin.site.site_title = admin.site.site_header = "Yummy Yard Administration"
admin.site.index_title = "Yummy Yard"