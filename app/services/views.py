from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins, permissions
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter

from users.models import User
from . import models, serializers
from .filters import ProfessionalFilter
from .models import InvestorServiceInfo
from .paginators import Pagination


class CategoryViewSet(mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Category.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CategorySerializer
    filterset_fields = ['direction']


class ProfessionalsViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    # TODO temporary ignore filter by bank details
    queryset = User.objects.filter(
        is_active=True,
        is_approved=True,
        user_services_info__generate_business=True,
        # bank_details__membership='premium',
        services__isnull=False,
        services__status='approved',
        profile__public_profile=True
    ).distinct()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = Pagination
    serializer_class = serializers.ProfessionalSerializer
    ordering_fields = ['user_services_info__followers', 'rating', 'price_start']
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = ProfessionalFilter


class UserServicesViewSet(mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.PublicUserServicesInfoSerializer
    queryset = User.objects.filter(
        is_active=True,
        is_approved=True,
        groups__name='User',
        user_services_info__generate_business=True,
        bank_details__membership='premium',
        services__isnull=False,
        services__status='approved',
        profile__public_profile=True
    ).distinct()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            user = queryset.get(pk=self.kwargs['pk'])
            if hasattr(user, 'user_services_info') and user.user_services_info:
                return user.user_services_info
        except User.DoesNotExist:
            raise NotFound


class InvestorServicesViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.InvestorServicesSerializer
    queryset = InvestorServiceInfo.objects.select_related('user').filter(
        user__is_active=True,
        user__is_approved=True,
        user__groups__name='Investor',
        # user__bank_details__isnull=False,
        user__investor_services_info__isnull=False,
        user__investor_services_info__reach_out=True,
        user__profile__public_profile=True
    ).distinct()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            return queryset.get(user__pk=self.kwargs['pk'])
        except User.DoesNotExist:
            raise NotFound
