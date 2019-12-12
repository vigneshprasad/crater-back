from rest_framework import viewsets, mixins, permissions

from . import models, serializers


class TagViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    queryset = models.Tag.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.TagSerializer
