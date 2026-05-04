from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import Graffiti, Photo, Vote
from .serializers import (
    GraffitiListSerializer,
    GraffitiDetailSerializer,
    GraffitiCreateUpdateSerializer,
    PhotoSerializer,
    VoteSerializer,
    VoteStatisticsSerializer,
)
from .permissions import IsOwnerOrReadOnly
from .filters import GraffitiFilterSet
from .pagination import GraffitiPagination


class GraffitiViewSet(viewsets.ModelViewSet):
    queryset = Graffiti.objects.prefetch_related('photos', 'votes').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = GraffitiFilterSet
    ordering = ['-created_at']
    pagination_class = GraffitiPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'search_radius']:
            permission_classes = [AllowAny]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GraffitiDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return GraffitiCreateUpdateSerializer
        return GraffitiListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def search_radius(self, request):
        """GET /api/graffiti/search_radius/?lat=50.45&lon=30.52&radius=5"""
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lon')
        radius = request.query_params.get('radius')

        if not all([latitude, longitude, radius]):
            return Response(
                {'error': 'Missing lat, lon, or radius parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except ValueError:
            return Response(
                {'error': 'lat, lon, radius must be numbers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.gis.geos import Point
        from django.contrib.gis.db.models.functions import Distance

        center_point = Point(longitude, latitude)
        radius_meters = radius * 1000

        queryset = self.get_queryset().filter(
            location__dwithin=(center_point, radius_meters)
        ).annotate(
            distance=Distance('location', center_point)
        ).order_by('distance')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        graffiti_id = self.kwargs.get('graffiti_id')
        graffiti = Graffiti.objects.filter(id=graffiti_id, author=self.request.user).first()
        if not graffiti:
            raise PermissionError('Graffiti not found or permission denied')
        serializer.save(graffiti=graffiti)


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        graffiti_id = self.kwargs.get('graffiti_id')
        graffiti = Graffiti.objects.get(id=graffiti_id)
        vote, created = Vote.objects.update_or_create(
            graffiti=graffiti,
            user=self.request.user,
            defaults={'vote_type': serializer.validated_data.get('vote_type')}
        )
        self.created = created

    @action(detail=False, methods=['get'])
    def statistics(self, request, graffiti_id=None):
        """GET /api/graffiti/{graffiti_id}/votes/statistics/"""
        graffiti_id = self.kwargs.get('graffiti_id')
        graffiti = Graffiti.objects.get(id=graffiti_id)
        exists_count = graffiti.votes.filter(vote_type='exists').count()
        not_exists_count = graffiti.votes.filter(vote_type='not_exists').count()
        return Response({
            'exists': exists_count,
            'not_exists': not_exists_count,
        })
