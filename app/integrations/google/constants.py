from django.conf import settings

from resources.meetings import choices

# Google API constants.
GOOGLE_API_CREDENTIALS = settings.GOOGLE_API_CREDENTIALS
GOOGLE_API_VERSION = "v3"
CALENDAR_SERVICE_NAME = "calendar"
CONFERENCE_DATA_VERSION = 1
DEFAULT_CALENDAR_ID = "hello@worknetwork.in"
SEND_UPDATE_TO_ALL = "all"

# Google Calender event constants.
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]
DEFAULT_SUMMARY_FOR_MEETING_EVENTS = "1:1_Professional Networking_WorkNetwork"
DEFAULT_DESCRIPTION_FOR_MEETING_EVENTS = "Hi, your 1:1 meeting has been scheduled for the above time. Please view " \
                                         "your inbox for an introduction to your match, their profile & the meeting " \
                                         "details ( an email from keziah@worknetwork.in would have been received). " \
                                         "In case you need to reschedule your meeting or for any other update, " \
                                         "please send an email on that thread to all participants. "
DEFAULT_TIMEZONE = "Asia/Kolkata"
HANGOUT_MEET = "hangoutsMeet"


CALENDAR_RESPONSE_STATUSES = (
    ('needsAction', 'needsAction'),
    ('declined', 'declined'),
    ('tentative', 'tentative'),
    ('accepted', 'accepted')
)

CALENDAR_RESPONSE_TO_MEETING_RSVP_STATUS_MAP = {
    'needsAction': choices.MEETING_RSVP_STATUS_PENDING,
    'declined': choices.MEETING_RSVP_STATUS_NOT_ATTENDING,
    'tentative': choices.MEETING_RSVP_STATUS_PENDING,
    'accepted': choices.MEETING_RSVP_STATUS_ATTENDING,
}

PENDING_CALENDAR_STATUSES = ['needsAction', 'declined', 'tentative']
ACCEPTED_CALENDAR_STATUSES = ['accepted']
