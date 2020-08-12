from datetime import time

OBJECTIVE_CHOICES = [
    ('meet_interesting_people', 'Meet Interesting People'),
    ('brainstorm_with_peers', 'Brainstorm with Peers'),
    ('business_development', 'Business Development'),
    ('start_a_company', 'Start a Company'),
    ('mentor_people', 'Mentor People'),
    ('find_mentors', 'Find Mentors')
]

DEFAULT_MEETING_TITLE = 'Meeting'
DEFAULT_ONE_ON_ONE_MEETING_TITLE = '1:1 Meeting'
DEFAULT_REGISTRATION_CLOSED_WEEKDAY = 1
DEFAULT_REGISTRATION_START_AND_WEEK_START_DELTA = 5
DEFAULT_TIME_SLOTS = {
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

MEETING_CHOICE_1_ON_1 = '1:1'

MEETING_TYPE_CHOICES = [
    (MEETING_CHOICE_1_ON_1, MEETING_CHOICE_1_ON_1),
]

ONE_ON_ONE_EMAIL_TEMPLATE = 'one_on_one_into_template'
