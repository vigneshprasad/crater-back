from django.db.models import Sum
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from users.paginators import Pagination
from . import models, serializers
from users import permissions


class TransactionViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    queryset = models.Transaction.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.TransactionSerializer
    pagination_class = Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Transaction.objects.none()
        return self.request.user.transactions.exclude(order__isnull=True).exclude(status='refund')

    @action(
        methods=['get'],
        serializer_class=serializers.TransactionStatisticSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=False
    )
    def statistic(self, request):
        transaction = self.get_queryset()
        data = {
            'received_sum': transaction.filter(direction='out').aggregate(Sum('amount'))['amount__sum'],
            'paid_sum': transaction.filter(direction='in').aggregate(Sum('amount'))['amount__sum']
        }
        return Response(data=data)
