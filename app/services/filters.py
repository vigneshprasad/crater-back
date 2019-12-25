from django_filters import rest_framework as filters

from .models import Service


class ServiceFilter(filters.FilterSet):
    price_from = filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_to = filters.NumberFilter(field_name="price", lookup_expr='lte')
    rating_from = filters.NumberFilter(field_name="rating", lookup_expr='gte')
    rating_to = filters.NumberFilter(field_name="rating", lookup_expr='lte')
    city = filters.NumberFilter(method='city_filter')

    class Meta:
        model = Service
        fields = [
            'price_from',
            'price_to',
            'rating_from',
            'rating_to',
            'city',

            'user_infos__industries',
            'service_type__group',
            'service_type__category'
        ]

    @staticmethod
    def city_filter(queryset, name, value):
        return queryset.filter(user__profile__work_city=value)

