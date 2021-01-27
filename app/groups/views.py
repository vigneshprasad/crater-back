import datetime
import pytz

from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from freelance.settings import TIME_ZONE

from users import permissions
from groups import models
from groups import serializers
from resources.meetings import receivers
from resources.meetings import signals


class CategoryViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.CategorySerializer
    queryset = models.Category.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]


class AgendaViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.AgendaSerializer
    queryset = models.Agenda.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]


class GroupsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.GroupSerializer
    queryset = models.Group.objects.filter(closed=False)
    permission_classes = [permissions.IsAuthenticated]


class InviteViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.AgendaSerializer
    queryset = models.Agenda.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]

    @action(
        methods=["post"],
        detail=False
    )
    def accepted(self, request, *args, **kwargs):
        return Response({"status": "success"})


class RequestViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.AgendaSerializer
    queryset = models.Agenda.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
