from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from integrations.onesignal import models, serializers
from users import permissions as user_permissions


class OneSignalDeviceViewSet(GenericViewSet):

    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    queryset = models.OneSignalDevice.objects.all()
    serializer_class = serializers.OneSignalDeviceSerializer

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[user_permissions.AllowAny]
    )
    def register(self, request):
        """Register a new device on backend."""
        data = request.data
        os_id = data.get("os_id")
        user = data.get("user", None)

        try:
            device, _ = models.OneSignalDevice.objects.update_or_create(
                os_id=os_id,
                defaults={"user_id": user}
            )
        except IntegrityError:
            message = {
                "status": 422,
                "message": "User device already registered"
            }
            return Response(message, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        serialized = self.get_serializer(device)
        return Response(serialized.data, status=status.HTTP_201_CREATED)
