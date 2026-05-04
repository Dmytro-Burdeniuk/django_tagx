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
