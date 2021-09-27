from django.conf import settings

from resources.meetings import choices

# Google API constants.
GOOGLE_API_CREDENTIALS = settings.GOOGLE_API_CREDENTIALS
GOOGLE_API_VERSION = "v3"
CALENDAR_SERVICE_NAME = "calendar"
CONFERENCE_DATA_VERSION = 1
# This version supports no conference data.
NO_CONFERENCE_DATA_VERSION = 0
DEFAULT_CALENDAR_ID = "hello@worknetwork.in"
SEND_UPDATE_TO_ALL = "all"

# Google Calender event constants.
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]

DEFAULT_ICON_URI_FOR_GOOGLE_EVENTS = "https://fonts.gstatic.com/s/i/productlogos/meet_2020q4/v6/web-512dp/logo_meet_2020q4_color_2x_web_512dp.png"

DEFAULT_CONFERENCE_NAME_FOR_MEETING = "1:1 Meeting"
DEFAULT_SUMMARY_FOR_MEETING = "{name1} <> {name2}| Professional Networking | WorkNetwork"
DEFAULT_DESCRIPTION_FOR_MEETING = "Hi, your 1:1 meeting has been scheduled for the above time. Please view " \
                                         "the app for an introduction to your match, their profile & the meeting " \
                                         "details (an email from meetings@worknetwork.in would have been received). " \
                                         "In case you need to reschedule your meeting or for any other update, " \
                                         "please send an email on that thread to all participants."


DEFAULT_CONFERENCE_NAME_FOR_CONVERSATIONS = "Conversation"
DEFAULT_SUMMARY_FOR_CONVERSATIONS = "Conversation on {topic_name} | WorkNetwork | Details in the description"
DEFAULT_DESCRIPTION_FOR_CONVERSATIONS = "Hi, your conversation has been scheduled for the above time. \n" \
                            "Format: Group Conversation.\n" \
                            "Location: Virtual, on the mobile app.\n" \
                            "Details: Visible under 'Your Conversations' on the app.\n" \
                            "Link to the app: {deeplink} \n" \
                            "Login details: Please use the email on this thread. \n" \
                            "Reschedule: Group conversation may not be rescheduled due to multiple participants."


DEFAULT_CONFERENCE_NAME_FOR_WEBINAR = "Live Stream"
ATTENDEE_SUMMARY_FOR_WEBINARS = "Live Stream with {creator_name} | {topic}."
ATTENDEE_DESCRIPTION_FOR_WEBINARS = "Hi, {creator_name} will go live at: \n\n " \
                                    "Date: {date} \n" \
                                    "Time: {time}. \n\n" \
                                    "Will be talking about: {topic}.\n\n"\
                                    "Where: Crater.Club \n\n" \
                                    "Link to the stream: {stream_link} \n\n" \
                                    "You can also view it on the mobile app {app_link}"

HOST_SUMMARY_FOR_WEBINARS = "Your Live Stream on Crater (WorkNetwork)."
HOST_DESCRIPTION_FOR_WEBINARS = "Hi, {creator_name} your live stream has been set up for \n\n:" \
                                "Date: {date} \n" \
                                "Time: {time}. \n\n" \
                                "Topic: {topic} \n\n" \
                                "Link to the stream: {stream_link} \n\n" \
                                "All you have to do is click on the link above & sign in with your number ( {phone_number}, everything else has been set up) \n\n" \
                                "If you need any help you have 2 points of contact, please feel free to call or whatsapp anytime: \n\n" \
                                "Vivan: +919930474469 \n" \
                                "Rajath:+917259137196 \n"

DEFAULT_TIMEZONE = "Asia/Kolkata"
HANGOUT_MEET = "hangoutsMeet"
ADD_ON_LINK = "addOn"


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
