from django.utils.translation import ugettext_lazy as _

PACKAGE_REQUEST_STATUS_CHOICES = (
    ('requested', _('Requested')),
    ('in_progress', _('In Progress')),
    ('rejected', _('Rejected')),
    ('completed', _('Completed')),
)