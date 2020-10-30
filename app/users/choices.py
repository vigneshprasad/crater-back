from django.utils.translation import ugettext_lazy as _

REASON_CHOICES = (
    ('18_year_old', _('I am at least 18 year old.')),
    ('join', _('I want to join the community to collaborate or share.')),
    ('understand', _('I understand the membership application process.')),
    ('can_verify_bank_account', _('I can verify a bank account & government-issued ID')),
    ('have_a_debit', _('I have a debit &/ or credit card')),
    ('investor_in_companies', _('I am qualified to sign up as an investor in companies')),
    (
        'connectionsare',
        _('I understand that no from of trading of equities take place on the platform, only connectionsare made')
    )
)

USER_GROUP = 'User'
INVESTOR_GROUP = 'Investor'

INTENT_NETWORK = 'network'
INTENT_SERVICES = 'services'

INTENT_CHOICES = (
    (INTENT_NETWORK, INTENT_NETWORK.title()),
    (INTENT_SERVICES, INTENT_SERVICES.title())
)

template_names = {
    'password_reset': 'Password reset',
    'verify_email': 'Verify email',
    'invite_friend': 'Invite Friend',
    'participate_event': 'Participate in Event',
    'two_weeks_subs_warning': 'Two weeks subs warning',
    'one_month_subs_warning': 'One month subs warning'
}

DEFAULT_LINKED_IN_URL = 'https://www.no-information.com/'


ADMIN_USER_EMAIL = 'admin@admin.com'


OS_NAME_ANDROID = 'ANDROID'
OS_NAME_IOS = 'IOS'
OS_NAME_WEB = 'WEB'

DEVICE_NAME_OTHER = 'Other'
DEVICE_NAME_WEB = 'WEB'

PASSWORD_RESET_FROM_EMAIL = "set-password@worknetwork.in"
