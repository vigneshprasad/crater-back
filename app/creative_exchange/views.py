from rest_framework import viewsets, mixins, permissions
from rest_framework.response import Response

from users.paginators import Pagination
from . import models, serializers


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
    queryset = models.ExchangeRequest.objects.filter(is_deleted=False).order_by('-id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeRequestSerializer
    pagination_class = Pagination
    detail_serializer_class = serializers.DetailExchangeRequestSerializer

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        context = self.get_serializer_context()
        serializer = self.detail_serializer_class(instance, **{'context': context})
        return Response(serializer.data)


class ExchangeResponseViewSet(mixins.CreateModelMixin,
                              mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    queryset = models.ExchangeResponse.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeResponseSerializer
    pagination_class = Pagination

    def get_queryset(self):
        return self.request.user.exchange_responses.all()

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        serializer.save()


class MyRequestsExchangeResponseViewSet(mixins.ListModelMixin,
                                        mixins.RetrieveModelMixin,
                                        viewsets.GenericViewSet):
    queryset = models.ExchangeResponse.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ExchangeResponseSerializer
    pagination_class = Pagination

    def get_queryset(self):
        return models.ExchangeResponse.objects.filter(request__user=self.request.user)
