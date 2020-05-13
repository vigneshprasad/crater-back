from allauth.account.models import EmailAddress
from django.contrib.auth import models as auth_models

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


class CheckGroupMixin:
    serializer = None

    def check_group(self):
        role = self.serializer.validated_data.get('role', 'user')
        if not self.user.groups.all().exists():
            try:
                group = auth_models.Group.objects.get(name=role.capitalize())
                self.user.groups.add(group)
            except auth_models.Group.DoesNotExist:
                pass


class CheckEmailMixin:
    serializer = None

    def check_email(self):
        email = self.serializer.validated_data.get('email', '')
        if self.user.email:
            address, created = EmailAddress.objects.get_or_create(user=self.user, email=self.user.email)
            address.verified = True
            address.save()
        if email and not self.user.email:
            self.user.email = email
            self.user.save()
