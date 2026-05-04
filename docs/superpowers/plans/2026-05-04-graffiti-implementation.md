# MVP Карта Графіті — План Реалізації

> **Для робочих:** ОБОВ'ЯЗКОВА НА-УМОВНІСТЬ: Використовуйте **superpowers:subagent-driven-development** або **superpowers:executing-plans** для реалізації цього плану задачу за задачею.

**Мета:** Реалізувати REST API для MVP карти графіті з аутентифікацією, геошуком та голосуванням.

**Архітектура:** Монолітна Django app з моделями (Graffiti, Photo, Vote), DRF ViewSets з дозволами, PostGIS для spatial queries, S3 для фотографій.

**Tech Stack:** Django 6.0+, DRF 3.17+, PostgreSQL + PostGIS, boto3 + django-storages, SimpleJWT (вже налаштовано).

---

## Task 1: Налаштування PostGIS в PostgreSQL та Django

**Файли:**
- Modify: `config/django/settings/base.py`
- Modify: `.env.example` та `.env`

- [ ] **Крок 1: Перевірити, що PostGIS встановлено в PostgreSQL**

```bash
psql -U postgres -d django_template -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

Очікуваний результат: `CREATE EXTENSION` (успішно) або `extension "postgis" already exists`.

- [ ] **Крок 2: Встановити необхідні пакети Python**

```bash
uv add django-gis
```

- [ ] **Крок 3: Добавити `django.contrib.gis` до INSTALLED_APPS**

Відкрити `/Users/dima/Projects/django_template/config/django/settings/base.py`.

Знайти секцію `INSTALLED_APPS` і додати **перед** іншими apps:

```python
INSTALLED_APPS = [
    'django.contrib.gis',  # ДОДАТИ ЦЕ ПЕРШИМ
    'django.contrib.admin',
    'django.contrib.auth',
    # ... rest of apps
    'apps.graffiti',       # ДОДАТИ ЦЬОГО ТЕЖ (для наступної task)
]
```

- [ ] **Крок 4: Налаштувати DATABASE для PostGIS**

В `config/django/settings/base.py`, знайти `DATABASES`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',  # ЗМІНИТИ ENGINE
        'NAME': os.environ.get('DB_NAME', 'django_template'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

- [ ] **Крок 5: Додати S3 конфігурацію в `config/django/settings/base.py`**

Додати в кінець файлу:

```python
# ===========================
# AWS S3 STORAGE (django-storages)
# ===========================
if os.environ.get('USE_S3', 'False') == 'True':
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': {
                'bucket_name': os.environ.get('AWS_STORAGE_BUCKET_NAME'),
                'region_name': os.environ.get('AWS_S3_REGION_NAME', 'us-east-1'),
                'access_key': os.environ.get('AWS_ACCESS_KEY_ID'),
                'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
                'custom_domain': os.environ.get('AWS_S3_CUSTOM_DOMAIN', None),
                'use_ssl': True,
            },
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
            'OPTIONS': {
                'location': os.path.join(BASE_DIR, 'media'),
            },
        },
    }

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

- [ ] **Крок 6: Встановити django-storages**

```bash
uv add "django-storages[s3]"
```

- [ ] **Крок 7: Оновити .env.example**

Додати в кінець файлу:

```bash
# AWS S3
USE_S3=False
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=graffiti-mvp-bucket
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=
```

- [ ] **Крок 8: Коміт**

```bash
git add config/django/settings/base.py .env.example
git commit -m "setup: PostGIS and S3 storage configuration"
```

---

## Task 2: Створити Django app `graffiti`

**Файли:**
- Create: `apps/graffiti/__init__.py`
- Create: `apps/graffiti/apps.py`
- Create: `apps/graffiti/admin.py`

- [ ] **Крок 1: Створити app за допомогою Django команди**

```bash
python manage.py startapp graffiti apps/graffiti
```

- [ ] **Крок 2: Перевірити, що файли створені**

```bash
ls -la apps/graffiti/
```

Очікуваний результат: `__init__.py`, `admin.py`, `apps.py`, `models.py`, `tests.py`, `views.py` та ін.

- [ ] **Крок 3: Оновити `apps/graffiti/apps.py`**

```python
from django.apps import AppConfig


class GraffitiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.graffiti'
```

- [ ] **Крок 4: Додати app до INSTALLED_APPS**

В `config/django/settings/base.py`:

```python
INSTALLED_APPS = [
    'django.contrib.gis',
    # ... інші apps
    'apps.graffiti',  # ДОДАТИ ЦЕ
]
```

- [ ] **Крок 5: Коміт**

```bash
git add apps/graffiti/
git commit -m "feat: create graffiti app"
```

---

## Task 3: Написати моделі (Graffiti, Photo, Vote)

**Файли:**
- Create/Modify: `apps/graffiti/models.py`

- [ ] **Крок 1: Написати модель Graffiti**

Замінити вміст `apps/graffiti/models.py` на:

```python
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.db.models import Index, Q

User = get_user_model()


class Graffiti(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='graffiti')
    location = models.PointField()  # PostGIS PointField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['author']),
            Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author.username}"
```

- [ ] **Крок 2: Додати модель Photo**

Додати в кінець `apps/graffiti/models.py`:

```python
class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    graffiti = models.ForeignKey(
        Graffiti, on_delete=models.CASCADE, related_name='photos'
    )
    image = models.ImageField(upload_to='graffiti_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Photo for {self.graffiti.title}"
```

- [ ] **Крок 3: Додати модель Vote**

Додати в кінець `apps/graffiti/models.py`:

```python
class Vote(models.Model):
    VOTE_CHOICES = [
        ('exists', 'Існує'),
        ('not_exists', 'Не існує'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4)
    graffiti = models.ForeignKey(
        Graffiti, on_delete=models.CASCADE, related_name='votes'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('graffiti', 'user')
        indexes = [
            Index(fields=['graffiti']),
            Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} voted {self.vote_type} on {self.graffiti.id}"
```

- [ ] **Крок 4: Додати моделі до admin (опціонально)**

В `apps/graffiti/admin.py`:

```python
from django.contrib import admin

from .models import Graffiti, Photo, Vote


@admin.register(Graffiti)
class GraffitiAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'description']


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['graffiti', 'uploaded_at']
    list_filter = ['uploaded_at']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['graffiti', 'user', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
```

- [ ] **Крок 5: Запустити makemigrations**

```bash
python manage.py makemigrations graffiti
```

Очікуваний результат: `Created migration 0001_initial.py`

- [ ] **Крок 6: Запустити migrate**

```bash
python manage.py migrate
```

Очікуваний результат: `OK` без помилок.

- [ ] **Крок 7: Коміт**

```bash
git add apps/graffiti/models.py apps/graffiti/admin.py apps/graffiti/migrations/
git commit -m "feat: create Graffiti, Photo, Vote models"
```

---

## Task 4: Написати serializers

**Файли:**
- Create: `apps/graffiti/serializers.py`

- [ ] **Крок 1: Створити serializers**

Створити новий файл `apps/graffiti/serializers.py`:

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Graffiti, Photo, Vote

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']
        read_only_fields = ['id', 'username']


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'vote_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class VoteStatisticsSerializer(serializers.Serializer):
    exists = serializers.IntegerField(read_only=True)
    not_exists = serializers.IntegerField(read_only=True)


class GraffitiListSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)
    votes_statistics = serializers.SerializerMethodField()

    class Meta:
        model = Graffiti
        fields = ['id', 'title', 'description', 'author', 'location', 'photos', 'votes_statistics', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_votes_statistics(self, obj):
        exists_count = obj.votes.filter(vote_type='exists').count()
        not_exists_count = obj.votes.filter(vote_type='not_exists').count()
        return {
            'exists': exists_count,
            'not_exists': not_exists_count,
        }


class GraffitiDetailSerializer(GraffitiListSerializer):
    photos = PhotoSerializer(many=True, read_only=True)
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Graffiti
        fields = ['id', 'title', 'description', 'author', 'location', 'photos', 'votes_statistics', 'user_vote', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            if vote:
                return {'id': str(vote.id), 'vote_type': vote.vote_type}
        return None


class GraffitiCreateUpdateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Graffiti
        fields = ['id', 'title', 'description', 'latitude', 'longitude', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        
        from django.contrib.gis.geos import Point
        validated_data['location'] = Point(longitude, latitude)
        validated_data['author'] = self.context['request'].user
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'latitude' in validated_data or 'longitude' in validated_data:
            from django.contrib.gis.geos import Point
            latitude = validated_data.pop('latitude', instance.location.y)
            longitude = validated_data.pop('longitude', instance.location.x)
            validated_data['location'] = Point(longitude, latitude)
        
        return super().update(instance, validated_data)
```

- [ ] **Крок 2: Коміт**

```bash
git add apps/graffiti/serializers.py
git commit -m "feat: create serializers for Graffiti, Photo, Vote"
```

---

## Task 5: Написати permissions та filters

**Файли:**
- Create: `apps/graffiti/permissions.py`
- Create: `apps/graffiti/filters.py`

- [ ] **Крок 1: Написати IsOwnerOrReadOnly permission**

Створити `apps/graffiti/permissions.py`:

```python
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Дозволяє редагування/видалення тільки власнику об'єкту.
    Читання дозволено всім.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
```

- [ ] **Крок 2: Написати GeometryFilter**

Створити `apps/graffiti/filters.py`:

```python
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models import F, Q
from django_filters import rest_framework as filters

from .models import Graffiti


class GraffitiFilterSet(filters.FilterSet):
    latitude = filters.NumberFilter(method='filter_by_radius', label='Latitude')
    longitude = filters.NumberFilter(method='filter_by_radius', label='Longitude')
    radius = filters.NumberFilter(
        method='filter_by_radius',
        label='Radius in kilometers',
        help_text='Search radius in kilometers'
    )

    class Meta:
        model = Graffiti
        fields = []

    def filter_by_radius(self, queryset, name, value):
        """
        Фільтр за радіусом (в км).
        Використовує PostGIS ST_DWithin функцію.
        """
        # Отримати параметри з request
        latitude = self.form.cleaned_data.get('latitude')
        longitude = self.form.cleaned_data.get('longitude')
        radius = self.form.cleaned_data.get('radius')

        if latitude and longitude and radius:
            # Конвертувати км в метри (для PostGIS)
            radius_meters = radius * 1000
            
            from django.contrib.gis.db.models import F, Value
            from django.contrib.gis.geos import Point
            from django.contrib.gis.db.models.functions import Distance, DWithin
            
            center_point = Point(longitude, latitude)
            
            # Фільтрувати по дистанції та додати дистанцію в результати
            queryset = queryset.filter(
                location__dwithin=(center_point, radius_meters)
            ).annotate(
                distance=Distance('location', center_point)
            ).order_by('distance')

        return queryset
```

- [ ] **Крок 3: Коміт**

```bash
git add apps/graffiti/permissions.py apps/graffiti/filters.py
git commit -m "feat: add IsOwnerOrReadOnly permission and GeometryFilter"
```

---

## Task 6: Написати ViewSets

**Файли:**
- Create: `apps/graffiti/views.py`

- [ ] **Крок 1: Написати GraffitiViewSet та інші**

Замінити вміст `apps/graffiti/views.py` на:

```python
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


class GraffitiViewSet(viewsets.ModelViewSet):
    queryset = Graffiti.objects.prefetch_related('photos', 'votes').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = GraffitiFilterSet
    ordering = ['-created_at']
    pagination_class = None  # Will add in next task

    def get_permissions(self):
        """
        list, retrieve → AllowAny (публічно читати)
        create → IsAuthenticated
        update, destroy → IsOwnerOrReadOnly
        """
        if self.action in ['list', 'retrieve']:
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

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def search_radius(self, request):
        """
        GET /api/graffiti/search_radius/?lat=50.45&lon=30.52&radius=5
        Пошук графіті в радіусі.
        """
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
        try:
            graffiti = Graffiti.objects.get(id=graffiti_id)
        except Graffiti.DoesNotExist:
            return Response(
                {'error': 'Graffiti not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Перевірити дозвіл
        if graffiti.author != self.request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(graffiti=graffiti)


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, graffiti_id=None):
        """
        Створити або оновити голос для графіті.
        Один голос на користувача.
        """
        try:
            graffiti = Graffiti.objects.get(id=graffiti_id)
        except Graffiti.DoesNotExist:
            return Response(
                {'error': 'Graffiti not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        vote, created = Vote.objects.update_or_create(
            graffiti=graffiti,
            user=request.user,
            defaults={'vote_type': request.data.get('vote_type')}
        )

        serializer = self.get_serializer(vote)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    @action(detail=False, methods=['get'])
    def statistics(self, request, graffiti_id=None):
        """
        GET /api/graffiti/{graffiti_id}/votes/statistics/
        Отримати статистику голосів.
        """
        try:
            graffiti = Graffiti.objects.get(id=graffiti_id)
        except Graffiti.DoesNotExist:
            return Response(
                {'error': 'Graffiti not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        exists_count = graffiti.votes.filter(vote_type='exists').count()
        not_exists_count = graffiti.votes.filter(vote_type='not_exists').count()

        return Response({
            'exists': exists_count,
            'not_exists': not_exists_count,
        })
```

- [ ] **Крок 2: Коміт**

```bash
git add apps/graffiti/views.py
git commit -m "feat: create ViewSets for Graffiti, Photo, Vote"
```

---

## Task 7: Налаштувати URL маршрути

**Файли:**
- Create: `apps/graffiti/urls.py`
- Modify: `config/urls.py`

- [ ] **Крок 1: Написати graffiti URLs**

Створити `apps/graffiti/urls.py`:

```python
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import GraffitiViewSet, PhotoViewSet, VoteViewSet

app_name = 'graffiti'

router = DefaultRouter()
router.register(r'graffiti', GraffitiViewSet, basename='graffiti')

urlpatterns = [
    path('', include(router.urls)),
]
```

- [ ] **Крок 2: Додати graffiti URLs до головного urls.py**

Відкрити `config/urls.py` и додати:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.graffiti.urls')),
    path('api/auth/', include('apps.authentication.urls')),  # Якщо вже є
]
```

- [ ] **Крок 3: Перевірити, що це запустить**

```bash
python manage.py runserver
```

Відкрити браузер і перейти на `http://localhost:8000/api/graffiti/`

Очікуваний результат: JSON список (пустий чи з даними).

- [ ] **Крок 4: Коміт**

```bash
git add apps/graffiti/urls.py config/urls.py
git commit -m "feat: setup graffiti API routes"
```

---

## Task 8: Додати pagination

**Файли:**
- Create: `apps/graffiti/pagination.py`
- Modify: `apps/graffiti/views.py`

- [ ] **Крок 1: Написати кастомний pagination клас**

Створити `apps/graffiti/pagination.py`:

```python
from rest_framework.pagination import PageNumberPagination


class GraffitiPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

- [ ] **Крок 2: Додати pagination до GraffitiViewSet**

Відкрити `apps/graffiti/views.py` і змінити:

```python
from .pagination import GraffitiPagination

class GraffitiViewSet(viewsets.ModelViewSet):
    # ... інші атрибути ...
    pagination_class = GraffitiPagination  # ЗМІНИТИ ЦЕ
```

- [ ] **Крок 3: Протестувати**

```bash
python manage.py runserver
```

Перейти на `http://localhost:8000/api/graffiti/?page=1`

Очікуваний результат: JSON з `count`, `next`, `previous`, `results`.

- [ ] **Крок 4: Коміт**

```bash
git add apps/graffiti/pagination.py apps/graffiti/views.py
git commit -m "feat: add page-based pagination"
```

---

## Task 9: Тестувати API вручну

**Файли:** Немає.

- [ ] **Крок 1: Отримати JWT токен**

```bash
# Скоріш за все вам потрібен існуючий юзер або створити тестовий
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'
```

- [ ] **Крок 2: Тестувати публічний список графіті**

```bash
curl -X GET http://localhost:8000/api/graffiti/
```

- [ ] **Крок 3: Тестувати створення графіті (з токеном)**

```bash
curl -X POST http://localhost:8000/api/graffiti/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "title": "Test Graffiti",
    "description": "A test graffiti location",
    "latitude": 50.45,
    "longitude": 30.52
  }'
```

- [ ] **Крок 4: Тестувати пошук в радіусі**

```bash
curl -X GET "http://localhost:8000/api/graffiti/search_radius/?lat=50.45&lon=30.52&radius=5"
```

---

## Task 10: Додати валідацію до serializers

**Файли:**
- Modify: `apps/graffiti/serializers.py`

- [ ] **Крок 1: Додати валідацію до GraffitiCreateUpdateSerializer**

- [ ] **Крок 2: Додати валідацію до PhotoSerializer**

- [ ] **Крок 3: Коміт**

---

## Task 11: Налаштування глобальної обробки помилок

**Файли:**
- Modify: `config/django/settings/base.py`

- [ ] **Крок 1: Додати REST_FRAMEWORK конфіг**

- [ ] **Крок 2: Коміт**

---

## Task 12: Додати API документацію (Swagger)

**Файли:**
- Modify: `config/django/settings/base.py`
- Modify: `config/urls.py`

- [ ] **Крок 1: Встановити drf-spectacular**

```bash
uv add drf-spectacular
```

- [ ] **Крок 2: Додати до INSTALLED_APPS та URLs**

- [ ] **Крок 3: Перевірити Swagger UI на /api/docs/**

- [ ] **Крок 4: Коміт**
