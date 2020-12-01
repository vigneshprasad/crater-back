from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.generics import CreateAPIView

from users import permissions
from rewards import models
from rewards import serializers


class PackagesViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      GenericViewSet):
    queryset = models.Package.objects.filter(is_active=True).order_by('order')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.PackageSerializer


class PackageRequestViewSet(CreateAPIView):
    queryset = models.PackageRequest.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.PackageRequestSerializer
