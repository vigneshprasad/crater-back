from datetime import time

OBJECTIVE_CHOICES = [
    ('meet_interesting_people', 'Meet interesting people'),
    ('brainstorm_with_peers', 'Brainstorm with Peers'),
    ('business_development', 'Business Development'),
    ('start_a_company', 'Start a Company'),
    ('mentor_people', 'Mentor People'),
    ('find_mentors', 'Find Mentors')
]

DEFAULT_MEETING_TITLE = 'Meeting'

DEFAULT_ONE_ON_ONE_MEETING_TITLE = '1:1 Meeting'

DEFAULT_TIME_SLOTS = {
    3: [
        {
            'start_time': time(12, 00, 00),
            'end_time': time(12, 30, 00)
        },
{
            'start_time': time(2, 00, 00),
            'end_time': time(2, 30, 00)
        },
{
            'start_time': time(4, 00, 00),
            'end_time': time(4, 30, 00)
        },
{
            'start_time': time(6, 00, 00),
            'end_time': time(6, 30, 00)
        },
{
            'start_time': time(7, 00, 00),
            'end_time': time(7, 30, 00)
        },
        {
            'start_time': time(8, 00, 00),
            'end_time': time(8, 30, 00)
        }
    ],
    4: [
    {
            'start_time': time(12, 00, 00),
            'end_time': time(12, 30, 00)
        },
    {
            'start_time': time(2, 00, 00),
            'end_time': time(2, 30, 00)
        },
    {
            'start_time': time(4, 00, 00),
            'end_time': time(4, 30, 00)
        },
    {
            'start_time': time(6, 00, 00),
            'end_time': time(6, 30, 00)
        },
{
            'start_time': time(7, 00, 00),
            'end_time': time(7, 30, 00)
        },
        {
            'start_time': time(8, 00, 00),
            'end_time': time(8, 30, 00)
        }
    ]
}
