from rest_framework import mixins
from rest_framework import viewsets

from crater.payments import models
from users import permissions as user_permissions
from crater.payments import serializers

# Create your views here.


class PaymentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = models.Payment.objects.all()
    permission_classes = [user_permissions.IsAuthenticated]
    serializer_class = serializers.PaymentSerializer

