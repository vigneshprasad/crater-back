from django.utils.translation import ugettext_lazy as _


SERVICE_STATUS = (
    ('approved', _('Approved')),
    ('declined', _('Declined')),
    ('unknown', _('No Decision')),
)
YEAR_OF_EXPERIENCE_CHOICES = (
    ('less_1_year', _('Less than 1 year')),
    ('1-2', _('1-2 years')),
    ('3-4', _('3-4 years')),
    ('5-7', _('5-7 years')),
    ('8-10', _('8-10 years'))
)
