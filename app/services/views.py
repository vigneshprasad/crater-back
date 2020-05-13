from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from order.models import Order
from users import permissions
from order.serializers import ReviewSerializer
from users.models import User
from . import models, serializers
from .filters import ProfessionalFilter
from .paginators import Pagination, ShortPagination


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
    ).distinct().order_by('profile__name')
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = Pagination
    serializer_class = serializers.ProfessionalSerializer
    ordering_fields = ['user_services_info__followers', 'rating', 'price_start']
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = ProfessionalFilter

    @action(
        methods=['get'],
        serializer_class=ReviewSerializer,
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=ShortPagination,
        detail=True
    )
    def reviews(self, request, pk):
        context = self.get_serializer_context()
        try:
            instance = self.queryset.get(pk=pk)
            order_with_reviews = Order.objects.filter(
                seller=instance, rate__isnull=False, status__in=['done', 'complete']
            ).order_by('-rate_datetime')
        except User.DoesNotExist:
            raise NotFound
        page = self.paginate_queryset(order_with_reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(
            ReviewSerializer(order_with_reviews, many=True, **{'context': context}).data
        )


class UserServicesViewSet(mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.PublicUserServicesInfoSerializer
    queryset = User.objects.filter(
        is_active=True,
        is_approved=True,
        groups__name='User',
        user_services_info__generate_business=True,
        # bank_details__membership='premium',
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
        except (User.DoesNotExist, ValidationError):
            raise NotFound


class InvestorServicesViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ProfessionalSerializer
    pagination_class = Pagination
    queryset = User.objects.filter(
        is_active=True,
        is_approved=True,
        groups__name='Investor',
        # bank_details__isnull=False,
        investor_services_info__isnull=False,
        investor_services_info__reach_out=True,
        profile__public_profile=True
    ).distinct()
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = ProfessionalFilter

    def get_object(self):
        self.serializer_class = serializers.InvestorServicesSerializer
        queryset = self.filter_queryset(self.get_queryset())
        try:
            user = queryset.get(pk=self.kwargs['pk'])
            if hasattr(user, 'investor_services_info') and user.investor_services_info:
                return user.investor_services_info
        except User.DoesNotExist:
            raise NotFound
