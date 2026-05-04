from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from debug_toolbar.toolbar import debug_toolbar_urls
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.django import base

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("api/", include("rest_framework.urls")),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/", include("apps.graffiti.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if base.DEBUG:
    urlpatterns.extend(debug_toolbar_urls())
