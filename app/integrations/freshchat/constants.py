from django.conf import settings

APPSFLYER_APP_LINK = "https://worknetwork.onelink.me/KbQv/AppStore"

# Freshchat Whatsapp details.
FRESHCHAT_BASE_URL = settings.FRESHCHAT_BASE_URL
FRESHCHAT_APP_ID = settings.FRESHCHAT_APP_ID
FRESHCHAT_ACCESS_TOKEN = settings.FRESHCHAT_ACCESS_TOKEN

FRESHCHAT_MESSAGING_PHONE_NUMBER = settings.FRESHCHAT_MESSAGING_PHONE_NUMBER
FRESHCHAT_WHATSAPP_NAMESPACE = settings.FRESHCHAT_WHATSAPP_NAMESPACE
FRESHCHAT_DEFAULT_PROVIDER = "whatsapp"

MEETING_CONFIRMATION_FRESHCHAT_TEMPLATE = "confirmation_of_appointment"

MEETING_CONFIRMATION_WITH_EMAIL_SENT = "meeting_confirmation_email"
# Deprecated.
MEETING_REMINDER_FRESHCHAT_TEMPLATE = "meeting_reminder_link"
MEETING_OPT_IN_REMINDER_TEMPLATE = "confirming_meeting"
# Deprecated
MEETING_CONFIRMATION_INTENT = "confirmation_of_11_intent"
MEETING_CONFIRMATION_RSVP_LINK = "meeting_confirmation_link"
# Deprecated
MEETING_CONFIRMATION_RSVP = "meeting_has_been_confirmed"
MEETING_REMINDER_RSVP_LINK = "meeting_unconfirmed_link"
# Deprecated.
REGISTRATION_CONFIRMATION = "registration_confirmation"

# Meeting registration updated.
MEETING_REGISTRATION_TEMPLATE = "confirmation_of_registration_updated"
MEETING_REGISTRATION_FREQUENCY_PLACEHOLDER = "1:1 meetings"
MEETING_REGISTRATION_DEFAULT_OBJECTIVE_TEXT = "Meet Interesting People"

# Meeting
MEETING_OPT_IN_TEMPLATE = "confirmation_of_meeting_preference"
MEETING_OPT_IN_MESSAGE = "clicking here: {}"
MEETING_OPT_IN_APP_LINK = "please use the app: {}"

# Meeting rsvp confirmation constants.
MEETING_CONFIRMATION_TEMPLATE = "meeting_has_been_confirmed"
MEETING_INFO_AVAILABILITY = "on the email thread and mobile app"

# Meeting cancellation constants.
MEETING_CANCELLATION_TEMPLATE = "cancellation_of_meeting"
MEETING_CANCELLATION_FALL_BACK = " if you believe this to be a mistake & have spoken to your match: please disregard the message"

# Reminder message constants.
MEETING_REMINDER_TEMPLATE = "reminder_of_upcoming_meeting"
MEETING_REMINDER_PREFILLED_MESSAGE_PROMPT = "Hey, I am on the meeting link shared by WorkNetwork for our meeting today. Would you be joining the meeting?"
MEETING_REMINDER_WHATSAPP_PROMPT_TEXT = "sending a whatsapp via this link: {}"
WHATSAPP_BASE_URL = "https://wa.me/"

# Meeting Reschedule communication constants.
MEETING_RESCHEDULE_REQUEST_TEMPLATE = "meeting_reschdule_request"
MEETING_RESCHEDULE_REQUEST_APPROVED_TEMPLATE = "meeting_reschdule_accepted"
MEETING_RESCHEDULE_REQUEST_DECLINED_TEMPLATE = "meeting_reschedule_cancellation"
MEETING_RESCHEDULE_REQUEST_DECLINED_PROMPT_MESSAGE = " if you have spoken to your match & believe this to be a mistake, please disregard the message."

# Conversation templates
CONVERSATION_CONFIRMATION_TEMPLATE = "huddle_meeting_setup_group"
CONVERSATION_REMINDER_TEMPLATE = "huddle_meeting_reminder_group"
CONVERSATION_PARTICIPANTS_APP_LINK = "View on the app: {}"
CONVERSATION_RSVP = "Please RSVP using the calendar invite. Note this meeting will take place on the mobile app."

# Freshchat API responses.
FRESHCHAT_STATUS_SUCCESS = 200
FRESHCHAT_STATUS_CREATED = 201
FRESHCHAT_STATUS_ACCEPTED = 202

# Possible message statuses.
FRESHCHAT_MESSAGE_ACCEPTED = 'ACCEPTED'
FRESHCHAT_MESSAGE_SENT = 'SENT'
FRESHCHAT_MESSAGE_DELIVERED = 'DELIVERED'
FRESHCHAT_MESSAGE_FAILED = 'FAILED'
FRESHCHAT_MESSAGE_IN_PROGRESS = 'IN_PROGRESS'

# If message response status is in these, it means that
# message is yet to be sent to the user.
FRESHCHAT_MESSAGE_PENDING_STATUSES = [
    FRESHCHAT_MESSAGE_ACCEPTED,
    FRESHCHAT_MESSAGE_IN_PROGRESS
]

# If message response status is in these, it means that
# message is successfully sent to the user.
FRESHCHAT_MESSAGE_SUCCESS_STATUSES = [
    FRESHCHAT_MESSAGE_DELIVERED,
    FRESHCHAT_MESSAGE_SENT
]

# If message response status is in these, it means that
# message sending has failed.
FRESHCHAT_MESSAGE_FAILURE_STATUSES = [
    FRESHCHAT_MESSAGE_FAILED,
]
