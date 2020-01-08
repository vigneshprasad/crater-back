from rest_framework import viewsets, mixins, permissions

from . import models, paginators, serializers


class OrderViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   viewsets.GenericViewSet):
    queryset = models.Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    pagination_class = paginators.Pagination

    def get_queryset(self):
        return self.request.user.buyer_orders.all()

    def perform_create(self, serializer):
        serializer.validated_data['buyer'] = self.request.user
        serializer.save()


class FundingRequestViewSet(mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            viewsets.GenericViewSet):
    queryset = models.FundingRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FundingRequestSerializer
    pagination_class = paginators.Pagination

    def get_queryset(self):
        return self.request.user.buyer_funding_requests.all()

    def perform_create(self, serializer):
        serializer.validated_data['buyer'] = self.request.user
        serializer.save()
