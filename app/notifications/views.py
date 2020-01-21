from rest_framework import viewsets, permissions, mixins
from rest_framework.response import Response

from . import models, serializers


class UserNotificationSettings(mixins.ListModelMixin,
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
