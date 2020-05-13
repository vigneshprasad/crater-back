from django_filters import rest_framework as django_filters
from rest_framework import viewsets, mixins
from users import permissions
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from order.models import Quote
from order.serializers import QuoteSerializer
from users.paginators import Pagination
from . import models, serializers, filters


class ExchangeCategoryViewSet(mixins.RetrieveModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    queryset = models.ExchangeCategory.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeCategorySerializer


class ExchangeRequestViewSet(mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             mixins.CreateModelMixin,
                             viewsets.GenericViewSet):
    queryset = models.ExchangeRequest.objects.filter(is_deleted=False).exclude(quotes__status='approved').order_by('-id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeRequestSerializer
    pagination_class = Pagination
    detail_serializer_class = serializers.DetailExchangeRequestSerializer
    filterset_class = filters.RequestFilter
    ordering_fields = ['created']
    filter_backends = (django_filters.DjangoFilterBackend, OrderingFilter)

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        context = self.get_serializer_context()
        serializer = self.detail_serializer_class(instance, **{'context': context})
        return Response(serializer.data)


class MyExchangeRequestViewSet(mixins.RetrieveModelMixin,
                               mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    queryset = models.ExchangeRequest.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeRequestSerializer
    pagination_class = Pagination
    detail_serializer_class = serializers.DetailExchangeRequestSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        context = self.get_serializer_context()
        serializer = self.detail_serializer_class(instance, **{'context': context})
        return Response(serializer.data)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.ExchangeRequest.objects.none()
        return self.request.user.exchange_requests.all()


class ExchangeQuoteViewSet(mixins.CreateModelMixin,
                           mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    queryset = Quote.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeQuoteSerializer
    pagination_class = Pagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Quote.objects.none()
        return self.request.user.seller_quotes.filter(exchange_request__isnull=False)

    def perform_create(self, serializer):
        serializer.validated_data['seller'] = self.request.user
        serializer.validated_data['buyer'] = serializer.validated_data['exchange_request'].user
        serializer.validated_data['status'] = 'provided'
        serializer.save()


class MyRequestsQuotesViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    queryset = Quote.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuoteSerializer
    pagination_class = Pagination
    filterset_fields = ['exchange_request']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Quote.objects.none()
        return (
            Quote.objects
            .filter(exchange_request__user=self.request.user, buyer=self.request.user)
            .order_by('-status')
        )
