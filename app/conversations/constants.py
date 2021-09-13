from datetime import time

GROUP_PRIVACY_PUBLIC = "public"
GROUP_PRIVACY_PRIVATE = "private"

GROUP_MEDIUM_AUDIO = "audio"
GROUP_MEDIUM_AUDIO_VIDEO = "audio & video"
GROUP_MEDIUM_CHAT = "chat"

DEFAULT_MAX_SPEAKERS = 6

INVITE_STATUS_PENDING = "pending"
INVITE_STATUS_ACCEPTED = "accepted"
INVITE_STATUS_DECLINED = "declined"

INVITE_TYPE_SPEAKER = "speaker"
INVITE_TYPE_ATTENDEE = "attendee"

EXTRA_EMAIL_FOR_INTRO_VERIFICATION = "hello@worknetwork.in"
MEETING_COMMUNICATION_FROM_EMAIL = "meetings@worknetwork.in"
MEETING_REPLY_EMAIL = "vivan@worknetwork.in"
GROUP_CONVERSATION_INTRODUCTION_TEMPLATE = "Group Conversation Introduction"
GROUP_CONVERSATION_FEEDBACK_TEMPLATE = "Group Conversation Feedback"

DEFAULT_TOPIC_NAME = "Default"

OBJECTIVE_TO_TOPIC_MAP = {
    "Marketing strategies": "Marketing strategies",
    "Product development": "Product management",
    "Career growth": "Building a business",
    "Financial planning": "Building a business",
    "Startup funding": "Startup funding",
    "Building a business": "Building a business",
    "Start a Company": "Building a business",
    "Explore shared interests": "Building a business",
    "Learn about specific industries": "Building a business",
    "Invest in companies / make investor introductions": "Startup funding",
    "Explore work & other partnerships": "Building a business",
    "Acquire customers": "Marketing strategies",
}
DEFAULT_APP_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

INSTANT_CONVERSATION_TIME_SLOTS = [
    time(14, 00, 00),
    time(16, 00, 00),
    time(18, 00, 00),
    time(20, 00, 00),
]

GROUP_TYPE_GENERIC_ENUM = 0
GROUP_TYPE_AMA_ENUM = 1


GROUP_TYPE_GENERIC = "Generic Group"
GROUP_TYPE_AMA = "AMA"

REQUEST_PARTICIPANT_SPEAKER_ENUM = 1
REQUEST_PARTICIPANT_ATTENDEE_ENUM = 2

REQUEST_PARTICIPANT_SPEAKER = "Speaker"
REQUEST_PARTICIPANT_ATTENDEE = "Attendee"

REQUEST_STATUS_PENDING_ENUM = 0
REQUEST_STATUS_ACCEPTED_ENUM = 1
REQUEST_STATUS_DECLINED_ENUM = 2

REQUEST_STATUS_PENDING = "pending"
REQUEST_STATUS_ACCEPTED = "accepted"
REQUEST_STATUS_DECLINED = "declined"
