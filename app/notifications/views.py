from django.core.exceptions import FieldError
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from order.serializers import EmptySerializer
from . import models, serializers, paginators
from .schema import batch_notification_read
from users import permissions


class UserNotificationSettingsViesSet(mixins.ListModelMixin,
                                      mixins.CreateModelMixin,
                                      viewsets.GenericViewSet):
    queryset = models.UserNotificationsSettings
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.UserNotificationsSettingsSerializer

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_object(self):
        return self.request.user.notification_settings

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data, instance=instance, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)


class NotificationViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = models.UserNotification.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.NotificationSerializer
    pagination_class = paginators.Pagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.UserNotification.objects.none()
        return self.request.user.notifications.filter(is_read=False)

    @action(
        methods=['post'],
        serializer_class=EmptySerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def read(self, request, pk):
        queryset = self.get_queryset()
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.is_read = True
            instance.save()
        except models.UserNotification.DoesNotExist:
            raise NotFound
        return Response(
            serializers.NotificationSerializer(instance, **{'context': context}).data
        )

    @swagger_auto_schema(request_body=batch_notification_read)
    @action(
        methods=['post'],
        serializer_class=serializers.NotificationSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=False
    )
    def read_all(self, request):
        queryset = self.get_queryset()
        try:
            filter_dict = {f'notification__{request.data["type"]}__isnull': False}
            instances = queryset.filter(**filter_dict).update(is_read=True)
        except (FieldError, KeyError):
            raise NotFound
        return Response({'updated': instances})
