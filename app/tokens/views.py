from django.db import IntegrityError
from rest_framework.decorators import action

from rest_framework.viewsets import GenericViewSet

from tokens import models, serializers
from users import permissions


class TokenDataPerDayViewSet(GenericViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = models.TokenDataPerDay.objects.all()
    serializer_class = serializers.TokenDataPerDaySerializer


class TokenTransactionViewSet(GenericViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = models.TokenTransaction.objects.all()
    serializer_class = serializers.TokenTransactionSerializer


class UserTokenLogViewSet(GenericViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = models.UserTokenLog.objects.all()
    serializer_class = serializers.UserTokenLogSerializer
