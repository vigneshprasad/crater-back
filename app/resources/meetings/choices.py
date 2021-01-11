from datetime import time
from django.utils.translation import ugettext_lazy as _

OBJECTIVE_CHOICES = [
    ('meet_interesting_people', 'Meet Interesting People'),
    ('brainstorm_with_peers', 'Brainstorm with Peers'),
    ('business_development', 'Business Development'),
    ('start_a_company', 'Start a Company'),
    ('mentor_people', 'Mentor People'),
    ('find_mentors', 'Find Mentors')
]

# Looking for means what you want to gain from the meeting.
# Looking to means what can you help people with.
OBJECTIVE_TYPES = (
    ('looking_for', _('Looking For')),
    ('looking_to', _('Looking To'))
)

DEFAULT_MEETING_TITLE = 'Meeting'
DEFAULT_ONE_ON_ONE_MEETING_TITLE = '1:1 Meeting'
DEFAULT_REGISTRATION_CLOSED_WEEKDAY = 1
DEFAULT_REGISTRATION_START_AND_WEEK_START_DELTA = 7
DEFAULT_MEETING_WEEK_DURATION = 6

DEFAULT_MEETING_TIME_SLOTS = {
    3: [
        {
            'start_time': time(12, 00, 00),
            'end_time': time(12, 30, 00)
        },
        {
            'start_time': time(14, 00, 00),
            'end_time': time(14, 30, 00)
        },
        {
            'start_time': time(16, 00, 00),
            'end_time': time(16, 30, 00)
        },
        {
            'start_time': time(18, 00, 00),
            'end_time': time(18, 30, 00)
        },
        {
            'start_time': time(19, 00, 00),
            'end_time': time(19, 30, 00)
        },
        {
            'start_time': time(20, 00, 00),
            'end_time': time(20, 30, 00)
        }
    ],
    4: [
        {
            'start_time': time(12, 00, 00),
            'end_time': time(12, 30, 00)
        },
        {
            'start_time': time(14, 00, 00),
            'end_time': time(14, 30, 00)
        },
        {
            'start_time': time(16, 00, 00),
            'end_time': time(16, 30, 00)
        },
        {
            'start_time': time(18, 00, 00),
            'end_time': time(18, 30, 00)
        },
        {
            'start_time': time(19, 00, 00),
            'end_time': time(19, 30, 00)
        },
        {
            'start_time': time(20, 00, 00),
            'end_time': time(20, 30, 00)
        }
    ]
}

MEETING_RSVP_STATUS_ATTENDING = 'attending'
MEETING_RSVP_STATUS_PENDING = 'pending'
MEETING_RSVP_STATUS_NOT_ATTENDING = 'not_attending'
MEETING_RSVP_STATUS_RESCHEDULE = 'reschedule'

MEETING_RSVP_UNCONFIRMED_STATUSES = [
    MEETING_RSVP_STATUS_PENDING,
    MEETING_RSVP_STATUS_NOT_ATTENDING,
    MEETING_RSVP_STATUS_RESCHEDULE,
]

MEETING_RSVP_DECLINED_STATUSES = [
    MEETING_RSVP_STATUS_PENDING,
    MEETING_RSVP_STATUS_NOT_ATTENDING,
]

MEETING_STATUS_CONFIRMED = 'confirmed'
MEETING_STATUS_CANCELLED = 'cancelled'
MEETING_STATUS_PENDING = 'pending'
MEETING_STATUS_RESCHEDULED = 'rescheduled'

RESCHEDULE_REQUEST_PENDING_APPROVAL = 'pending_approval'
RESCHEDULE_REQUEST_CONFIRMED = 'confirmed'
RESCHEDULE_REQUEST_DECLINED = 'declined'

MEETING_UNCONFIRMED_STATUSES = (
    MEETING_STATUS_PENDING,
    MEETING_STATUS_RESCHEDULED,
)

MEETING_STATUS_CHOICES = (
    (MEETING_STATUS_CONFIRMED, MEETING_STATUS_CONFIRMED.title()),
    (MEETING_STATUS_CANCELLED, MEETING_STATUS_CANCELLED.title()),
    (MEETING_STATUS_PENDING, MEETING_STATUS_PENDING.title()),
    (MEETING_STATUS_RESCHEDULED, MEETING_STATUS_RESCHEDULED.title()),
)

MEETING_RSVP_STATUS_CHOICES = (
    (MEETING_RSVP_STATUS_ATTENDING, _(MEETING_RSVP_STATUS_ATTENDING.title())),
    (MEETING_RSVP_STATUS_PENDING, _(MEETING_RSVP_STATUS_PENDING.title())),
    (MEETING_RSVP_STATUS_NOT_ATTENDING, _(MEETING_RSVP_STATUS_NOT_ATTENDING.title())),
    (MEETING_RSVP_STATUS_RESCHEDULE, _(MEETING_RSVP_STATUS_RESCHEDULE.title())),
)

# Reschedule request possible statuses.
RESCHEDULE_REQUEST_STATUSES = (
    (RESCHEDULE_REQUEST_PENDING_APPROVAL, RESCHEDULE_REQUEST_PENDING_APPROVAL.title()),
    (RESCHEDULE_REQUEST_CONFIRMED, RESCHEDULE_REQUEST_CONFIRMED.title()),
    (RESCHEDULE_REQUEST_DECLINED, RESCHEDULE_REQUEST_DECLINED.title()),
)

# These slots are only used for display purposes.
DEFAULT_DISPLAY_TIME_SLOTS = {
    3: [
        {
            'start_time': time(14, 00, 00),
            'end_time': time(14, 30, 00)
        },
        {
            'start_time': time(16, 00, 00),
            'end_time': time(16, 30, 00)
        },
        {
            'start_time': time(18, 00, 00),
            'end_time': time(18, 30, 00)
        },
        {
            'start_time': time(20, 00, 00),
            'end_time': time(20, 30, 00)
        }
    ],
    4: [
        {
            'start_time': time(14, 00, 00),
            'end_time': time(14, 30, 00)
        },
        {
            'start_time': time(16, 00, 00),
            'end_time': time(16, 30, 00)
        },
        {
            'start_time': time(18, 00, 00),
            'end_time': time(18, 30, 00)
        },
        {
            'start_time': time(20, 00, 00),
            'end_time': time(20, 30, 00)
        }
    ],
    5: [
        {
            'start_time': time(16, 00, 00),
            'end_time': time(16, 30, 00)
        }
    ]
}

RESCHEDULE_WEEKDAY_TIME_SLOT_MAP = [
    time(14, 00, 00),
    time(16, 00, 00),
    time(18, 00, 00),
    time(20, 00, 00),
]


MEETING_CHOICE_1_ON_1 = '1:1'

MEETING_TYPE_CHOICES = [
    (MEETING_CHOICE_1_ON_1, MEETING_CHOICE_1_ON_1),
]

ONE_ON_ONE_INTRODUCTION_EMAIL_TEMPLATE = '1:1 Meeting Introduction'
ONE_ON_ONE_FEEDBACK_EMAIL_TEMPLATE = '1:1 Meeting Feedback'
ONE_ON_ONE_MEETING_CANCELED_TEMPLATE = '1:1 Meeting Canceled'
ONE_ON_ONE_MEETING_CONFIRMED_TEMPLATE = "1:1 Meeting Confirmed"
ONE_ON_ONE_OPT_IN_EMAIL_TEMPLATE = '1:1 Opt In'
MEETING_WEEKLY_REWARDS_TEMPLATE = 'Meeting Points Weekly'
MEETINGS_INTRO_FROM_EMAIL = 'keziah@worknetwork.in'
MEETING_COMMUNICATION_FROM_EMAIL = 'meetings@worknetwork.in'
MEETINGS_OPT_IN_FROM_EMAIL = 'hello@worknetwork.in'
EXTRA_EMAIL_FOR_INTRO_VERIFICATION = 'hello@worknetwork.in'
MEETING_REWARDS_FROM_EMAIL = 'rewards@worknetwork.in'

MAX_MEMBER_FOR_ONE_ON_ONE = 2
