class CheckDeviceMixin:

    def check_device(self):
        pass

    # def check_device(self):
    #     os_id = self.serializer.validated_data.get('os_id', '')
    #     application = self.serializer.validated_data.get('application', 'client')
    #     if os_id:
    #         device, created = models.Device.objects.get_or_create(user=self.user, os_id=os_id, application=application)
    #         if not created:
    #             device.is_active = True
    #             device.save()
