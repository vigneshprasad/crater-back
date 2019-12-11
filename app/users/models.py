import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

from users.managers import UserManager
from . import choices


class User(AbstractUser):
    """
    Extends Abstract User model with additional fields.
    Makes authentication with email and password fields.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    username = models.CharField(_('Username'), max_length=150)
    email = models.EmailField(_('Email'), unique=True, null=True)
    name = models.CharField(_('Name'), max_length=255)
    city = models.ForeignKey(
        'locations.City',
        verbose_name=_('City'),
        null=True,
        related_name='users',
        on_delete=models.SET_NULL
    )
    reason = models.CharField(
        max_length=100,
        verbose_name=_('Reason'),
        choices=choices.REASON_CHOICES,
        null=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'users'
        ordering = ('date_joined',)

    def send_reset_password_email(self):
        data = {
            'uid': urlsafe_base64_encode(force_bytes(self.pk)),
            'user': self,
            'token': default_token_generator.make_token(self)
        }
        # TODO: use Mailchip/Mandrill service when service will created
        pass

