from allauth.account.models import EmailAddress
from django.contrib.auth import models as auth_models

from . import models
from . import choices

from wn_analytics import models as wn_analytics_models


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

class SetIntentMixin:
    serializer = None

    def set_intent(self):
        if self.user.intent:
            return

        intent = self.serializer.validated_data.get('intent', choices.INTENT_NETWORK)
        self.user.intent = intent
        self.user.save()


class SetSourceMixin:
    serializer = None

    def set_source(self):
        utm_source = self.serializer.validated_data.get('utm_source')
        utm_campaign = self.serializer.validated_data.get('utm_campaign')
        
        if not (utm_source or utm_campaign):
            return
        
        wn_analytics_models.UserSource.objects.create(
            user=self.user,
            utm_source=utm_source,
            utm_campaign=utm_campaign
        )


class PhoneVerifiedMixin:
    serializer = None

    def set_phone_verified(self):
        self.user.phone_number_verified = True
        self.user.save()