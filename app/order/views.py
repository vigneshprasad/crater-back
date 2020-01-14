from django.http import Http404
from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from . import models, paginators, serializers


class BuyerOrderViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = models.Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Quote.objects.none()
        return self.request.user.buyer_orders.exclude(status='created')

    def perform_create(self, serializer):
        serializer.validated_data['buyer'] = self.request.user
        serializer.save()


class SellerOrderViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    queryset = models.Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Order.objects.none()
        return self.request.user.seller_orders.exclude(status='created')

    @action(
        methods=['post'],
        serializer_class=serializers.AcceptOrderSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def accept(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raize_exception=True)
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'accepted'
            note = serializer.validated_data.get('note')
            if note:
                instance.note = note
            instance.save()
        except models.Order.DoesNotExist:
            raise Http404
        return Response(
            serializers.OrderSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=None,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def cancel(self, request, pk):
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'canceled'
            instance.save()
        except models.Order.DoesNotExist:
            raise Http404
        return Response(
            serializers.OrderSerializer(instance, **{'context': context}).data
        )


class CartOrderViewSet(mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    queryset = models.Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Order.objects.none()
        return self.request.user.buyer_orders.filter(
            status='created',
            quote__isnull=True,
            creative_exchange_response__isnull=True
        )


class BuyerQuoteViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = models.Quote.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.QuoteSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Quote.objects.none()
        return self.request.user.buyer_quotes.all()

    def perform_create(self, serializer):
        serializer.validated_data['buyer'] = self.request.user
        serializer.save()

    @action(
        methods=['post'],
        serializer_class=serializers.ProvideQuoteSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def accept(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raize_exception=True)
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'provided'
            instance.save()
        except models.Quote.DoesNotExist:
            raise Http404
        return Response(
            serializers.QuoteSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=None,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def cancel(self, request, pk):
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'canceled'
            instance.save()
        except models.Quote.DoesNotExist:
            raise Http404
        return Response(
            serializers.QuoteSerializer(instance, **{'context': context}).data
        )


class SellerQuoteViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    queryset = models.Quote.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.QuoteSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Quote.objects.none()
        return self.request.user.seller_quotes.all()

    @action(
        methods=['post'],
        serializer_class=serializers.ProvideQuoteSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def provide(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raize_exception=True)
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'provided'
            instance.save()
        except models.Quote.DoesNotExist:
            raise Http404
        return Response(
            serializers.QuoteSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=None,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def cancel(self, request, pk):
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'canceled'
            instance.save()
        except models.Quote.DoesNotExist:
            raise Http404
        return Response(
            serializers.QuoteSerializer(instance, **{'context': context}).data
        )


class BuyerFundingRequestViewSet(mixins.RetrieveModelMixin,
                                 mixins.ListModelMixin,
                                 mixins.CreateModelMixin,
                                 viewsets.GenericViewSet):
    queryset = models.FundingRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FundingRequestSerializer
    pagination_class = paginators.Pagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.FundingRequest.objects.none()
        return self.request.user.buyer_funding_requests.all()

    def perform_create(self, serializer):
        serializer.validated_data['buyer'] = self.request.user
        serializer.save()


class InvestorFundingRequestViewSet(mixins.RetrieveModelMixin,
                                    mixins.ListModelMixin,
                                    viewsets.GenericViewSet):
    queryset = models.FundingRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FundingRequestSerializer
    pagination_class = paginators.Pagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.FundingRequest.objects.none()
        return self.request.user.funding_requests.all()

    @action(
        methods=['post'],
        serializer_class=None,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def accept(self, request, pk):
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'accepted'
            instance.save()
        except models.FundingRequest.DoesNotExist:
            raise Http404
        return Response(
            serializers.FundingRequestSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=None,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def cancel(self, request, pk):
        queryset = self.get_queryset().filter(status__in=['pending'])
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'canceled'
            instance.save()
        except models.FundingRequest.DoesNotExist:
            raise Http404
        return Response(
            serializers.FundingRequestSerializer(instance, **{'context': context}).data
        )
