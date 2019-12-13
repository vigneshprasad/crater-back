import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from users.managers import UserManager
from utils.validators import SizeValidator
# from utils.mandrill_service import mandrill_service
from . import choices


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
        # mandrill_service.send_email(
        #     template_name='password_reset',
        #     content=data,
        #     to=[
        #         {
        #             "email": self.email,
        #             "name": self.name,
        #             "type": "to"
        #         }
        #     ]
        # )
        # TODO: use Mailchip/Mandrill service when service will created
        pass

    @property
    def has_profile(self):
        return hasattr(self, 'profile') and self.profile

    @property
    def full_registered(self):
        status = (
            self.has_profile
        )
        return status


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
        verbose_name=_('Tag lime'),
        max_length=100,
        null=True,
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
        null=True,
        verbose_name=_('Additional Information')
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

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')


@receiver(pre_save, sender=User)
def create_push_and_rent(sender, instance, *args, **kwargs):
    if not instance.name:
        instance.name = f'{instance.first_name} {instance.last_name}'
    return instance
