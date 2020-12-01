from django.db import models
from django.core import exceptions
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from colorfield.fields import ColorField

from base import models as base_model
from rewards import choices


class PackageProvider(base_model.BaseModel):
    """
    Package provider for a certain package deal

    Note:
        This can be a service provider(User)
        on the platform or not
    """
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='package_provide',
        null=True,
        blank=True,
    )
    name = models.CharField(_('Name'), max_length=255)
    description = models.CharField(_('Description'), max_length=800)
    logo = models.ImageField(verbose_name=_('Logo'))

    def __str__(self):
        return self.name


class Package(base_model.BaseModel):
    """
    Package deals available for users

    """
    max_price = models.PositiveIntegerField(
        verbose_name=_('Max Price'),
        validators=[MaxValueValidator(99999999), MinValueValidator(1)]
    )
    max_discount = models.PositiveIntegerField(
        verbose_name=_('Max Discount'),
        validators=[MaxValueValidator(99999999), MinValueValidator(1)]
    )
    max_discount_points = models.PositiveIntegerField(
        verbose_name=_('Points for Max Discount'),
        validators=[MaxValueValidator(999999), MinValueValidator(1)]
    )
    title = models.CharField(max_length=255)
    short_desc = models.CharField(_('Short Description'), max_length=800)
    list_image = models.ImageField(verbose_name=_('List Image'))
    cover_image = models.ImageField(verbose_name=_('Cover Image'))
    color = ColorField(default='#FFAC3B')
    provider = models.ForeignKey(
        'rewards.PackageProvider',
        on_delete=models.CASCADE,
        related_name='packages',
        verbose_name=_('Package Provider')
    )
    long_desc = models.TextField(
        verbose_name=_('Long Description'),
    )
    is_active = models.BooleanField(
        verbose_name=_('is Active'),
        default=True,
    )
    is_dark = models.BooleanField(
        verbose_name=_('Dark Theme'),
        default=True,
    )
    show_on_web = models.BooleanField(
        verbose_name=_('Show on Web'),
        default=False,
    )
    order = models.PositiveIntegerField(
        verbose_name=_('Order'),
        default=0,
    )

    @property
    def points_conversion(self):
        return self.max_discount / self.max_discount_points

    def __str__(self):
        return self.title


class PackageRequest(base_model.BaseModel):
    """
    Model to track request of Package made by User

    TODO(Abhishek): Integrate this model with Order from Services in V2

    """
    quantity = models.PositiveIntegerField(
        verbose_name=_('Quantity'),
        validators=[MaxValueValidator(999), MinValueValidator(1)],
    )
    requested_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='package_requests',
        verbose_name=_('Requested By')
    )
    package = models.ForeignKey(
        'rewards.Package',
        on_delete=models.CASCADE,
        related_name='requests',
        verbose_name=_('Package')
    )
    point_applied = models.PositiveIntegerField(
        verbose_name=_('Point Applied'),
        validators=[MaxValueValidator(999999), MinValueValidator(1)],
    )
    status = models.CharField(
        verbose_name=_('Request Status'),
        choices=choices.PACKAGE_REQUEST_STATUS_CHOICES,
        default=choices.PACKAGE_REQUEST_STATUS_CHOICES[0][0],
        max_length=255,
    )

    def clean(self):
        if self.point_applied > self.requested_by.points.points:
            raise exceptions.ValidationError({'end': _('Points Applied cannot be greater than points held by user.')})
        if self.point_applied > (self.package.max_discount_points * self.quantity):
            raise exceptions.ValidationError({'end': _('Points Applied cannot be greater than max points for package.')})

    def payable_amount(self):
        return self.package.max_price - (self.point_applied * self.package.points_conversion)

    def __str__(self):
        return "{} - {}".format(
            self.package.title,
            self.status,
        )

