from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins, permissions
from rest_framework.filters import OrderingFilter

from . import models, serializers
from .filters import ServiceFilter
from .paginators import Pagination


class CategoryViewSet(mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Category.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CategorySerializer
    filterset_fields = ['direction']


class ServiceViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Service.objects.filter(
        status='approved',
        user_infos__generate_business=True,
        user__bank_details__membership='premium',
        user__is_approved=True,
        user__is_active=True
    )
    pagination_class = Pagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ProfessionalServiceSerializer
    ordering_fields = ['price', 'rating']
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = ServiceFilter

