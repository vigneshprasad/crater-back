from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from django.db import IntegrityError

from integrations.onesignal import models
from integrations.onesignal import serializers

from users import permissions


class OneSignalDeviceViewSet(GenericViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = models.OneSignalDevice.objects.all()
    serializer_class = serializers.OneSignalDeviceSerializer

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[permissions.AllowAny]
    )
    def register(self, request):
        data = request.data
        os_id = data.get("os_id")
        user = data.get("user", None)

        try:
            device, _ = models.OneSignalDevice.objects.update_or_create(
                os_id=os_id,
                defaults={
                    "user_id": user
                }
            )
            serialized = self.get_serializer(device)
        except IntegrityError:
            message = {
                "status": 422,
                "message": "User device already registered"
            }
            return Response(message, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(serialized.data, status=status.HTTP_201_CREATED)
