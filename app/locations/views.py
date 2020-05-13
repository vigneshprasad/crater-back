from rest_framework import viewsets, mixins
from users import permissions

from . import models, serializers


class CityViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = models.City.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CitySerializer
    filterset_fields = ['is_work']
