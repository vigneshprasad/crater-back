from rest_framework import serializers

from integrations.onesignal import models


class OneSignalDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.OneSignalDevice
        fields = (
            "id",
            "user",
            "os_id"
        )