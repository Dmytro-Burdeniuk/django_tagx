from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from debug_toolbar.toolbar import debug_toolbar_urls

from config.django import base

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("api/", include("rest_framework.urls")),
    path("api/auth/", include("apps.authentication.urls")),
]

if base.DEBUG:
    urlpatterns.extend(debug_toolbar_urls())
