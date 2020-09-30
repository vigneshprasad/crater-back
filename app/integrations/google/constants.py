from django.conf import settings

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
DEFAULT_SUMMARY_FOR_MEETING_EVENTS = "1:1 WorkNetwork"
DEFAULT_DESCRIPTION_FOR_MEETING_EVENTS = "1:1 WorkNetwork"
DEFAULT_TIMEZONE = "Asia/Kolkata"
HANGOUT_MEET = "hangoutsMeet"
