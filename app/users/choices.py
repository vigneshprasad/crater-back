from django.utils.regex_helper import Choice
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

TYPEFORM_URL_TO_SOURCE_MAP = {
    "https://worknetwork.typeform.com/to/MNbvcw7y": "MF1: LP_TF",
    "https://worknetwork.typeform.com/to/CN4xKZL8": "MF2: D_TF",
    "https://worknetwork.typeform.com/to/ltoxdMaX": "MF3: LI_OR"
}

# Education level constants.
EDUCATION_LEVEL_HIGH_SCHOOL = "High School"
EDUCATION_LEVEL_UNDERGRADUATE = "Undergraduate"
EDUCATION_LEVEL_MASTERS = "Masters"
EDUCATION_LEVEL_MBA = "MBA"
EDUCATION_LEVEL_PHD = "PHD"

EDUCATION_LEVEL_HIGH_SCHOOL_ENUM = 0
EDUCATION_LEVEL_UNDERGRADUATE_ENUM = 1
EDUCATION_LEVEL_MASTERS_ENUM = 2
EDUCATION_LEVEL_MBA_ENUM = 3
EDUCATION_LEVEL_PHD_ENUM = 4

# Years of experience constants.
EXPERIENCE_ONE_TO_TWO_YEARS = "0-2"
EXPERIENCE_THREE_TO_FIVE_YEARS = "3-5"
EXPERIENCE_SIX_TO_TEN_YEARS = "6-10"
EXPERIENCE_ELEVEN_TO_FIFTEEN_YEARS = "11-15"
EXPERIENCE_SIXTEEN_TO_TWENTY_YEARS = "16-20"
EXPERIENCE_TWENTY_ONE_TO_THIRTY_YEARS = "21-30"
EXPERIENCE_THIRTY_PLUS_YEARS = "30+"


EXPERIENCE_ONE_TO_TWO_YEARS_ENUM = 0
EXPERIENCE_THREE_TO_FIVE_YEARS_ENUM = 1
EXPERIENCE_SIX_TO_TEN_YEARS_ENUM = 2
EXPERIENCE_ELEVEN_TO_FIFTEEN_YEARS_ENUM = 3
EXPERIENCE_SIXTEEN_TO_TWENTY_YEARS_ENUM = 4
EXPERIENCE_TWENTY_ONE_TO_THIRTY_YEARS_ENUM = 5
EXPERIENCE_THIRTY_PLUS_YEARS_ENUM = 6

# Company type constants.
COMPANY_TYPE_NOT_EMPLOYED = "Not Employed"
COMPANY_TYPES_START_UP = "Startup"
COMPANY_TYPE_MNC = "MNC"
COMPANY_TYPE_SME = "SME"
COMPANY_TYPE_CONSULTANCY = "Consultancy/Funds"

COMPANY_TYPE_NOT_EMPLOYED_ENUM = 0
COMPANY_TYPES_START_UP_ENUM = 1
COMPANY_TYPE_MNC_ENUM = 2
COMPANY_TYPE_SME_ENUM = 3
COMPANY_TYPE_CONSULTANCY_ENUM = 4
