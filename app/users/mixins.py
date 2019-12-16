from . import models


class CheckDeviceMixin:
    serializer = None

    def check_device(self):
        os_id = self.serializer.validated_data.get('os_id', '')
        if os_id:
            device, created = models.Device.objects.get_or_create(
                user=self.user, os_id=os_id,
            )
            if not created:
                device.is_active = True
                device.save()
