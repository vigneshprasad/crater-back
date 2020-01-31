from django_filters import rest_framework as filters

from users.models import User


class ProfessionalFilter(filters.FilterSet):
    price_from = filters.NumberFilter(field_name='price_start', lookup_expr='gte')
    price_to = filters.NumberFilter(field_name='price_start', lookup_expr='lte')
    city = filters.NumberFilter(method='city_filter')
    category = filters.NumberFilter(method='category_filter')
    followers_from = filters.NumberFilter(field_name='user_services_info__followers', lookup_expr='gte')
    followers_to = filters.NumberFilter(field_name='user_services_info__followers', lookup_expr='lte')

    class Meta:
        model = User
        fields = [
            'price_to',
            'price_from',
            'followers_from',
            'followers_to',
            'category',
            'city',
            'user_services_info__industries',
            'user_services_info__services__service_type'

        ]

    @staticmethod
    def category_filter(queryset, name, value):
        return queryset.filter(services__status='approved', services__service_type__category=value)

    @staticmethod
    def city_filter(queryset, name, value):
        return queryset.filter(profile__work_city=value)
