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

MEETING_RSVP_STATUS_CHOICES = (
    ('attending', _('Attending')),
    ('pending', _('Pending')),
    ('not_attending', _('Not Attending')),
    ('reschedule', _('Reschedule')),
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


MEETING_CHOICE_1_ON_1 = '1:1'

MEETING_TYPE_CHOICES = [
    (MEETING_CHOICE_1_ON_1, MEETING_CHOICE_1_ON_1),
]

ONE_ON_ONE_INTRODUCTION_EMAIL_TEMPLATE = '1:1 Meeting Introduction'
ONE_ON_ONE_FEEDBACK_EMAIL_TEMPLATE = '1:1 Meeting Feedback'
ONE_ON_ONE_OPT_IN_EMAIL_TEMPLATE = '1:1 Opt In'
MEETINGS_INTRO_FROM_EMAIL = 'keziah@worknetwork.in'
MEETINGS_OPT_IN_FROM_EMAIL = 'hello@worknetwork.in'
EXTRA_EMAIL_FOR_INTRO_VERIFICATION = 'hello@worknetwork.in'

MAX_MEMBER_FOR_ONE_ON_ONE = 2
