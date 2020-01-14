from django.utils.translation import ugettext_lazy as _

QUOTE_STATUS_CHOICES = (
    ('pending', _('Pending')),
    ('provided', _('Provided')),
    ('accepted', _('Accepted')),
    ('canceled', _('Canceled')),
)

ORDER_STATUS_CHOICES = (
    ('created', _('Created')),  # Not paid order
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
