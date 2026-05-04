from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import GraffitiViewSet, PhotoViewSet, VoteViewSet

app_name = 'graffiti'

router = DefaultRouter()
router.register(r'graffiti', GraffitiViewSet, basename='graffiti')

urlpatterns = [
    path('', include(router.urls)),
]
