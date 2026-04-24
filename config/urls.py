from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from config.django import base

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
]

if base.DEBUG:
    urlpatterns.extend(debug_toolbar_urls())
