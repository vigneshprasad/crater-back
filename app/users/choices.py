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

# Source constants.
BASE_SOURCE_FACEBOOK = "Facebook"
BASE_SOURCE_LINKEDIN = "Linkedin"
BASE_SOURCE_BUMBLE = "Bumble"
BASE_SOURCE_REFERRAL = "Referral"
BASE_SOURCE_ORGANIC = "Organic"


BASE_SOURCE_TO_SCORE_MAP = {
    BASE_SOURCE_FACEBOOK: 50,
    BASE_SOURCE_LINKEDIN: 100,
    BASE_SOURCE_REFERRAL: 80,
    BASE_SOURCE_BUMBLE: 70,
    BASE_SOURCE_ORGANIC: 50
}

TYPEFORM_URL_TO_SOURCE_MAP = {
    "https://worknetwork.typeform.com/to/H8wMoIyV": ("Linkedin", "Linkedin Women"),
    "https://worknetwork.typeform.com/to/oh1lVxPJ": ("Linkedin", "Linkedin Helper(Yash)"),
    "https://worknetwork.typeform.com/to/LorqbZPS": ("Linkedin", "Linkedin Helper(Keziah)"),
    "https://worknetwork.typeform.com/to/ltoxdMaX": ("Linkedin", "Linkedin Manual"),
    "https://worknetwork.typeform.com/to/Xdvnp8bO": ("Bumble", "Bumble Bizz"),
    "https://worknetwork.typeform.com/to/CN4xKZL8": ("Facebook", "Facebook: F2 Direct to TF"),
    "https://worknetwork.typeform.com/to/MNbvcw7y": ("Facebook", "Facebook: F1 Landing page to TF"),
    "https://worknetwork.typeform.com/to/YbWuCTJy": ("Facebook", "Facebook: Exp Funnel"),
}

EXISTING_SOURCES_TO_NEW_SOURCE_MAP = {
    "MF1: LP_TF": ("Facebook", "Facebook: F1 Landing page to TF"),
    "MF2: D_TF": ("Facebook", "Facebook: F2 Direct to TF"),
    "MF3: LI_OR": ("Linkedin", "Linkedin Manual"),
    "F2 - TYPEFORM": ("Facebook", "Facebook: F2 Direct to TF"),
    "F2-TYPEFORM": ("Facebook", "Facebook: F2 Direct to TF"),
    "typeform": ("Facebook", "Facebook: F1 Landing page to TF"),
    "https://worknetwork.typeform.com/to/H8wMoIyV": ("Linkedin", "Linkedin Women"),
    "https://worknetwork.typeform.com/to/oh1lVxPJ": ("Linkedin", "Linkedin Helper(Yash)"),
    "https://worknetwork.typeform.com/to/LorqbZPS": ("Linkedin", "Linkedin Helper(Keziah)"),
    "https://worknetwork.typeform.com/to/ltoxdMaX": ("Linkedin", "Linkedin Manual"),
    "https://worknetwork.typeform.com/to/Xdvnp8bO": ("Bumble", "Bumble Bizz"),
    "https://worknetwork.typeform.com/to/CN4xKZL8": ("Facebook", "Facebook: F2 Direct to TF"),
    "https://worknetwork.typeform.com/to/MNbvcw7y": ("Facebook", "Facebook: F1 Landing page to TF"),
    "https://worknetwork.typeform.com/to/YbWuCTJy": ("Facebook", "Facebook: Exp Funnel"),
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

EDUCATION_LEVEL_STR_TO_ENUM = {
    EDUCATION_LEVEL_HIGH_SCHOOL: EDUCATION_LEVEL_HIGH_SCHOOL_ENUM,
    EDUCATION_LEVEL_UNDERGRADUATE: EDUCATION_LEVEL_UNDERGRADUATE_ENUM,
    EDUCATION_LEVEL_MASTERS: EDUCATION_LEVEL_MASTERS_ENUM,
    EDUCATION_LEVEL_MBA: EDUCATION_LEVEL_MBA_ENUM,
    EDUCATION_LEVEL_PHD: EDUCATION_LEVEL_PHD_ENUM
}

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

EXPERIENCE_STR_TO_ENUM = {
    EXPERIENCE_ONE_TO_TWO_YEARS: EXPERIENCE_ONE_TO_TWO_YEARS_ENUM,
    EXPERIENCE_THREE_TO_FIVE_YEARS: EXPERIENCE_THREE_TO_FIVE_YEARS_ENUM,
    EXPERIENCE_SIX_TO_TEN_YEARS: EXPERIENCE_SIX_TO_TEN_YEARS_ENUM,
    EXPERIENCE_ELEVEN_TO_FIFTEEN_YEARS: EXPERIENCE_ELEVEN_TO_FIFTEEN_YEARS_ENUM,
    EXPERIENCE_SIXTEEN_TO_TWENTY_YEARS: EXPERIENCE_SIXTEEN_TO_TWENTY_YEARS_ENUM,
    EXPERIENCE_TWENTY_ONE_TO_THIRTY_YEARS: EXPERIENCE_TWENTY_ONE_TO_THIRTY_YEARS_ENUM,
    EXPERIENCE_THIRTY_PLUS_YEARS: EXPERIENCE_THIRTY_PLUS_YEARS_ENUM
}

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

COMPANY_TYPE_STR_ENUM = {
    COMPANY_TYPE_NOT_EMPLOYED: COMPANY_TYPE_NOT_EMPLOYED_ENUM,
    COMPANY_TYPES_START_UP: COMPANY_TYPES_START_UP_ENUM,
    COMPANY_TYPE_MNC: COMPANY_TYPE_MNC_ENUM,
    COMPANY_TYPE_SME: COMPANY_TYPE_SME_ENUM,
    COMPANY_TYPE_CONSULTANCY: COMPANY_TYPE_CONSULTANCY_ENUM
}

# Sector constants.
SECTOR_TYPE_ACCOUNTS = "Accounts"
SECTOR_TYPE_AGRICULTURE = "Agriculture"
SECTOR_TYPE_AI = "AI"
SECTOR_TYPE_BIO = "Bio"
SECTOR_TYPE_CHEMICAL = "Chemical"
SECTOR_TYPE_COMPUTER = "Computer"
SECTOR_TYPE_CONSULTING = "Consulting"
SECTOR_TYPE_DATA = "Data"
SECTOR_TYPE_DESIGN = "Design"
SECTOR_TYPE_E_COMMERCE = "E-commerce"
SECTOR_TYPE_EDUCATION = "Education"
SECTOR_TYPE_ELECTRICAL = "Electrical"
SECTOR_TYPE_ENERGY = "Energy"
SECTOR_TYPE_ENVIRONMENT = "Environment"
SECTOR_TYPE_EVENT = "Event"
SECTOR_TYPE_FASHION = "Fashion"
SECTOR_TYPE_FILM = "Film"
SECTOR_TYPE_FINANCE = "Financial"
SECTOR_TYPE_FOOD = "Food"
SECTOR_TYPE_GAMING = "Gaming"
SECTOR_TYPE_HEALTH = "Health"
SECTOR_TYPE_HR = "HR"
SECTOR_TYPE_INVESTOR = "Investor"
SECTOR_TYPE_LAW = "Law"
SECTOR_TYPE_MARKETING = "Marketing"
SECTOR_TYPE_MECHANICAL = "Mechanical"
SECTOR_TYPE_MEDIA = "Media"
SECTOR_TYPE_MENTAL_HEALTH = "Mental Health"
SECTOR_TYPE_PHOTOGRAPHY = "Photography"
SECTOR_TYPE_POLITICS = "Politics"
SECTOR_TYPE_PRODUCT = "Product"
SECTOR_TYPE_REAL_ESTATE = "Real Estate"
SECTOR_TYPE_SOCIAL = "Social"
SECTOR_TYPE_STARTUP = "Startup"
SECTOR_TYPE_TRAVEL = "Travel"
