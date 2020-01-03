from django.utils.translation import ugettext_lazy as _

ORDER_STATUS_CHOICES = (
    ('created', _('Created')),
    ('pending', _('Pending')),
    ('canceled', _('Canceled')),
    ('accepted', _('Accepted')),
    ('complete', _('Complete')),
)

FUNDING_REQUEST_CHOICES = (
    ('pending', _('Pending')),
    ('canceled', _('Canceled')),
    ('accepted', _('Accepted'))
)
