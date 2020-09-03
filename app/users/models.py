import datetime
import uuid

import exrex
from allauth.account.models import EmailAddress, EmailConfirmation
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField

from notifications.models import UserNotificationsSettings
from payment.models import Subscription
from users.managers import UserManager
from utils.user_secret_key import create_new_secret_key
from utils.validators import SizeValidator
from . import choices
from .tasks import send_twilio_message, send_unique_push, send_email, start_transcoding_for_cover_file
from freelance.settings import DEFAULT_FROM_EMAIL


class User(AbstractUser):
    """
    Extends Abstract User model with additional fields.
    Makes authentication with email and password fields.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    username = models.CharField(_('Username'), max_length=150)
    email = models.EmailField(_('Email'), unique=True, null=True)
    name = models.CharField(_('Name'), max_length=100)
    city = models.ForeignKey(
        'tags.CityProxy',
        verbose_name=_('City'),
        null=True,
        related_name='users',
        on_delete=models.SET_NULL
    )
    objectives = models.ManyToManyField(
        'tags.Objective',
        verbose_name=_('Objectives')
    )
    reason = models.CharField(
        max_length=400,
        verbose_name=_('Reason'),
        null=True,
        blank=True
    )
    source = models.CharField(
        max_length=400,
        verbose_name=_('Source'),
        null=True,
        blank=True
    )
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_('Phone number')
    )
    phone_number_verified = models.BooleanField(
        default=False,
        verbose_name=_('Phone Number Verified')
    )
    new_phone_number = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_('Phone number')
    )
    sms_code = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Sms code'),
        max_length=4
    )
    referer = models.ForeignKey(
        'users.User',
        verbose_name=_('Referer'),
        related_name='referrals',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_staff = models.BooleanField(
        _('Admin'),
        default=False,
        help_text=_('Admin permissions, can be restricted by superadmin.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Banned/Unbanned User.'
        ),
    )
    is_approved = models.BooleanField(
        _('Approved'),
        default=False,
        help_text=_(
            'User Approval.'
        ),
    )
    is_service_approved = models.BooleanField(
        _('Service Approved'),
        default=False,
        help_text=_(
            'User Service Approval.'
        ),
    )
    rating = models.FloatField(
        verbose_name=_('Rating'),
        null=True,
        blank=True
    )
    price_start = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Price start')
    )
    pan_card = models.ImageField(
        null=True,
        blank=True,
        verbose_name=_('Pan card'),
        upload_to='user/pan_card/%Y/%m/%d'
    )
    auth_secret_key = models.CharField(
        max_length=255,
        verbose_name=_('Secret key'),
        null=True,
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'users'
        ordering = ('date_joined',)

    @staticmethod
    def send_email(
            subject,
            to,
            template_name,
            content,
            merge_vars,
            **kwargs
    ):
        # Update merge vars with Front URL.
        for d in merge_vars.values():
            d.update({'front_url': settings.FRONT_URL})

        send_email.delay(
            subject=subject,
            to=to,
            template_name=template_name,
            content=content,
            merge_vars=merge_vars,
            **kwargs
        )

    def send_reset_password_email(self):
        data = {
            self.email: {
                'uid': urlsafe_base64_encode(force_bytes(self.pk)),
                'name': self.name,
                'token': default_token_generator.make_token(self)
            }
        }
        self.send_email(subject='Password reset', to=[self.email],
                        template_name=choices.template_names.get('password_reset'), content={},
                        merge_vars=data)

    def get_phone_number(self):
        """Returns phone number string if present."""
        return self.phone_number.as_e164 if self.phone_number else None

    @property
    def has_profile(self):
        """Checking if the user has profile object.

        Note:
            First this function check for the raw object and then
            checks if the profile is saved in the DB. If any of
            these conditions are not met, it returns False.

        """
        has_profile_object = bool(hasattr(self, 'profile') and self.profile)
        if not has_profile_object:
            return False
        if not self.profile.pk:
            return False
        return True

    @property
    def has_points(self):
        return bool(hasattr(self, 'points') and self.points)

    @property
    def profile_completed(self):
        status = (
            self.has_profile
            and
            self.phone_number
            and
            self.phone_number_verified
            and
            self.email_verified
            and
            self.is_approved
        )
        return status

    @property
    def has_bank_details(self):
        return bool(hasattr(self, 'bank_details') and self.bank_details)

    @property
    def has_introduction(self):
        status = (
            self.has_profile
            and 
            hasattr(self.profile, 'introduction') 
            and 
            self.profile.introduction
        )
        return bool(status)

    @property
    def full_registered(self):
        status = (
            self.has_profile
            and
            self.has_bank_detais
            and
            self.has_services
        )
        return status

    @property
    def has_services(self):
        if self.role == 'user':
            return bool(hasattr(self, 'user_services_info') and self.user_services_info)
        elif self.role == 'investor':
            return bool(hasattr(self, 'investor_services_info') and self.investor_services_info)
        return None

    @property
    def has_active_subscription(self):
        return self.subscriptions.filter(is_active=True).exists()

    @property
    def active_subscription_membership(self):
        active_subscription = self.subscriptions.filter(is_active=True).first()
        if active_subscription:
            return active_subscription.membership
        return None

    @property
    def role(self):
        if self.groups.filter(name='Investor').exists():
            return 'investor'
        if self.groups.filter(name='User').exists():
            return 'user'
        return None

    @staticmethod
    def _send_sms(phone_number, message):
        send_twilio_message.delay(str(phone_number), message)

    def send_sms(self, message):
        self._send_sms(str(self.phone_number), message)

    def send_push(self, data, message):
        devices = self.devices.filter(is_active=True)
        for device in devices:
            send_unique_push.delay(
                device.os_id,
                {
                    'en': message,
                    # 'ru': translate('ru', message)
                },
                data=data
            )

    def send_verify_email(self):
        email_address, created = EmailAddress.objects.get_or_create(
            user=self, email__iexact=self.email, defaults={"email": self.email}
        )
        confirmation = EmailConfirmation.create(email_address=email_address)
        confirmation.sent = timezone.now()
        confirmation.save()
        data = {
            self.email: {
                'key': confirmation.key,
                'name': self.name
            }
        }
        self.send_email(subject='Verify your email', to=[self.email],
                        template_name=choices.template_names.get('verify_email'), content={},
                        merge_vars=data)

    @property
    def email_verified(self):
        return self.emailaddress_set.filter(email=self.email, verified=True).exists()

    def generate_sms_code(self, commit=True):
        code = exrex.getone('[1-9]{4}')
        if settings.DEBUG:
            code = '1111'
        self.sms_code = code
        if commit:
            self.save()

    @property
    def rating_count(self):
        return self.seller_orders.filter(status='complete', rate__isnull=False).count()

    def recalculate_rating(self):
        rates = list(self.seller_orders.filter(status='complete', rate__isnull=False).values_list('rate', flat=True))
        rate = 0
        if rates:
            rate = sum(filter(lambda x: x, rates)) / len(rates)
            self.rating = round(rate, 2)
            self.save()
        return round(rate, 2)

    def refresh_auth_secret_key(self, commit=True):
        self.auth_secret_key = create_new_secret_key()
        if commit:
            self.save()

    def __str__(self):
        if self.email:
            return self.email
        else:
            return '<no-email>'
    

class Device(TimeStampedModel):
    user = models.ForeignKey(
        'users.User',
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='devices',
        null=True
    )
    os_id = models.CharField(
        _('One signal id'),
        max_length=150
    )
    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = _('User Device')
        verbose_name_plural = _('User Devices')

    def __str__(self):
        return f'{self.user.username} {self.os_id}'


class UserDeviceInfo(TimeStampedModel):
    user = models.ForeignKey(
        'users.User',
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='device_info'
    )
    # Ex. Android, iOS, WEB.
    os = models.CharField(
        max_length=32,
        null=True,
        blank=True
    )
    # OS version.
    os_version = models.CharField(
        max_length=32,
        null=True,
        blank=True
    )
    # Device being used.
    device_name = models.CharField(
        max_length=256,
        null=True,
        blank=True
    )
    # Model number or the device.
    device_model = models.CharField(
        max_length=256,
        null=True,
        blank=True
    )
    # What type of device is this.
    type = models.CharField(
        max_length=32,
        null=True,
        blank=True
    )
    # When this device was last used.
    last_used = models.DateTimeField(
        default=timezone.now
    )

    class Meta:
        ordering = ('-last_used', )

    def get_os_info(self):
        return "{} {}".format(
            self.os or '',
            self.os_version or ''
        )

    def get_device_info(self):
        return "{} {}".format(
            self.device_name or '',
            self.device_model or ''
        )


class Profile(models.Model):
    user = models.OneToOneField(
        'users.User',
        related_name='profile',
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Company Name')
    )
    tag_line = models.CharField(
        verbose_name=_('Tag line'),
        max_length=100,
        blank=True,
        null=True
    )
    photo = models.ImageField(
        upload_to='profile/photo/%Y/%m/%d',
        verbose_name=_('Photo'),
        null=True,
        blank=True,
        validators=[SizeValidator(size=30)]
    )
    photo_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Photo Url'),
        max_length=1024
    )
    cover = models.ForeignKey(
        'users.CoverFile',
        null=True,
        blank=True,
        verbose_name=_('Cover File'),
        related_name='profiles',
        on_delete=models.SET_NULL
    )
    introduction = models.CharField(
        max_length=800,
        verbose_name=_('Introduction'),
        blank=True,
        null=True
    )
    focus = models.CharField(
        max_length=800,
        verbose_name=_('Focus'),
        blank=True,
        null=True
    )
    additional_information = models.CharField(
        max_length=800,
        verbose_name=_('Additional Information'),
        blank=True,
        null=True
    )
    linkedin_url = models.CharField(
        verbose_name=_('Linked In'),
        blank=True,
        null=True,
        max_length=800
    )
    instagram = models.CharField(
        verbose_name=_('Instagram'),
        null=True,
        blank=True,
        max_length=800
    )
    instagram_id = models.CharField(
        verbose_name=_('Instagram Id'),
        null=True,
        blank=True,
        max_length=32
    )
    instagram_username = models.CharField(
        blank=True,
        null=True,
        max_length=400,
        verbose_name=_('Instagram username')
    )
    twitter = models.CharField(
        verbose_name=_('Twitter'),
        blank=True,
        null=True,
        max_length=255
    )
    work_city = models.ForeignKey(
        'tags.WorkCityProxy',
        null=True,
        blank=True,
        verbose_name=_('Work city'),
        on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(
        'tags.Tag',
        verbose_name=_('Tags'),
        related_name='profiles'
    )
    public_profile = models.BooleanField(
        default=True,
        verbose_name=_('Public Profile')
    )
    public_introduction = models.TextField(
        max_length=1024,
        verbose_name=_('Public Introduction'),
        blank=True,
        null=True
    )
    interests = models.ManyToManyField(
        'tags.Interests',
        verbose_name=_('Interests')
    )
    opted_in_for_whatsapp = models.BooleanField(
        default=True,
        verbose_name=_('Whatsapp Messaging Enabled')
    )

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profile')

    def __str__(self):
        return self.name

    @property
    def is_instagram_set(self):
        return bool(self.instagram)

    def get_introduction(self):
        return (self.public_introduction
                if self.public_introduction else self.introduction)

    def get_photo_url(self):
        return self.photo.url if self.photo else self.photo_url


class Referral(TimeStampedModel):
    """
    Set referral relations between Users
    """
    user = models.OneToOneField(
        'users.User',
        verbose_name=_('Referral'),
        on_delete=models.CASCADE
    )
    amount = models.CharField(
        _('Total referral subscription amount'),
        null=True,
        max_length=100,
    )
    is_paid = models.BooleanField(_('Is paid'), default=False)
    is_rewarded = models.BooleanField(_('Is rewarded'), default=False)

    class Meta:
        verbose_name = _('Referral')
        verbose_name_plural = _('Referrals')
        ordering = ['user__referer__name']


class Admin(User):
    proxy = True

    class Meta:
        verbose_name = _('Admin')
        verbose_name_plural = _('Admins')


class CoverFile(TimeStampedModel):
    file = models.FileField(
        upload_to='profile/cover/%Y/%m/%d/',
        verbose_name=_('Cover'),
        null=True,
        validators=[SizeValidator(size=512)],
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        related_name='cover_files'
    )
    cover_thumbnail = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Cover thumbnail')
    )
    cover_transcoder = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Cover transcoder')
    )
    transcoder_job_id = models.CharField(
        max_length=255,
        verbose_name=_('Transcoder job id'),
        null=True,
        blank=True
    )
    transcoder_job_success = models.BooleanField(
        default=False
    )
    transcoder_uuid = models.UUIDField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.file.name if self.file else ' - '


@receiver(post_save, sender=CoverFile)
def profile_post_save(sender, instance, created,  *args, **kwargs):
    if created:
        transaction.on_commit(lambda: start_transcoding_for_cover_file.delay(instance.pk))


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created,  *args, **kwargs):
    if not (hasattr(instance, 'notification_settings') and instance.notification_settings):
        UserNotificationsSettings.objects.create(user=instance)
    if created and not instance.subscriptions.filter(is_active=True):
        Subscription.objects.create(
            user=instance,
            date_start=timezone.now().date(),
            date_end=datetime.date(2020, 12, 1),
        )
