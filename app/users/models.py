import uuid

import exrex
from allauth.account.models import EmailAddress, EmailConfirmation, EmailConfirmationHMAC
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField

from users.managers import UserManager
from utils.validators import SizeValidator
from . import choices
from .tasks import send_twilio_message, send_unique_push, send_email


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
        'locations.City',
        verbose_name=_('City'),
        null=True,
        related_name='users',
        on_delete=models.SET_NULL
    )
    reason = models.CharField(
        max_length=400,
        verbose_name=_('Reason'),
        null=True
    )
    phone_number = PhoneNumberField(
        blank=True,
        verbose_name=_('Phone number')
    )
    sms_code = models.CharField(
        blank=True,
        verbose_name=_('Sms code'),
        max_length=4
    )
    phone_number_verified = models.BooleanField(
        default=False,
        verbose_name=_('Phone Number Verified')
    )
    referer = models.ForeignKey(
        'users.User',
        verbose_name=_('Referer'),
        related_name='referrals',
        on_delete=models.CASCADE,
        null=True
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'users'
        ordering = ('date_joined',)

    def send_email(self,
                   subject,
                   to,
                   template_name,
                   content,
                   merge_vars,
                   from_email='no-reply@fwmail.scenario-projects.com'):
        send_email.delay(
            subject=subject,
            to=to,
            template_name=template_name,
            content=content,
            merge_vars=merge_vars,
            from_email=from_email
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

    @property
    def has_profile(self):
        return hasattr(self, 'profile') and self.profile

    @property
    def has_bank_details(self):
        return hasattr(self, 'bank_details') and self.bank_details

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
            return hasattr(self, 'user_services_info') and self.user_services_info
        elif self.role == 'investor':
            return hasattr(self, 'investor_services_info') and self.investor_services_info
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
        send_twilio_message.delay(phone_number, message)

    def send_sms(self, message):
        self._send_sms(self.phone_number, message)

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
        try:
            email_address = EmailAddress.objects.get_for_user(self, self.email)
        except EmailAddress.DoesNotExist:
            email_address = EmailAddress.objects.create(self, self.email, verified=False)
        confirmation = EmailConfirmationHMAC(email_address)
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


class Profile(models.Model):
    user = models.OneToOneField(
        'users.User',
        related_name='profile',
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )
    tag_line = models.CharField(
        verbose_name=_('Tag line'),
        max_length=100,
        blank=True
    )
    photo = models.ImageField(
        upload_to='profile/photo/%Y/%m/%d',
        verbose_name=_('Photo'),
        null=True,
        validators=[SizeValidator(size=30)]
    )
    cover = models.FileField(
        upload_to='profile/cover/%Y/%m/%d',
        verbose_name=_('Cover'),
        null=True,
        validators=[SizeValidator(size=512)]
    )
    introduction = models.CharField(
        max_length=800,
        verbose_name=_('Introduction'),
        blank=True
    )
    focus = models.CharField(
        max_length=800,
        verbose_name=_('Focus'),
        blank=True
    )
    additional_information = models.CharField(
        max_length=800,
        verbose_name=_('Additional Information'),
        blank=True
    )
    instagram = models.URLField(
        verbose_name=_('Instagram'),
        blank=True
    )
    twitter = models.URLField(
        verbose_name=_('Twitter'),
        blank=True
    )
    work_city = models.ForeignKey(
        'locations.City',
        null=True,
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

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profile')

    def __str__(self):
        return self.name


class Admin(User):
    proxy = True

    class Meta:
        verbose_name = _('Admin')
        verbose_name_plural = _('Admins')
