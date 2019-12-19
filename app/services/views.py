from rest_framework import viewsets, mixins, permissions

from . import models, serializers


class CategoryViewSet(mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Category.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CategorySerializer
