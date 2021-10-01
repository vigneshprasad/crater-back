from django.conf import settings

DYTE_PROD_BASE_URL = settings.DYTE_PROD_BASE_URL
DYTE_JOIN_MEETING_BASE_URL = settings.DYTE_JOIN_MEETING_BASE_URL

DATETIME_EXCHANGE_FORMAT = "YYYY-MM-DDThh:mm:ss.SSSZ"

DYTE_ORG_ID = settings.DYTE_ORD_ID
DYTE_APP_ID = settings.DYTE_APP_ID

DEFAULT_PRESET_NAME = "participant"

DEFAULT_WEBINAR_PRESET_NAME = "webinar_view_preset"
DEFAULT_WEBINAR_PARTICIPANT_PRESET_NAME = "default_webinar_participant_preset"
DEFAULT_WEBINAR_HOST_PRESET_NAME = "default_webinar_host_preset"

DYTE_EVENT_MEETING_STARTED = "meeting.started"
DYTE_EVENT_MEETING_ENDED = "meeting.ended"
DYTE_EVENT_PARTICIPANT_JOINED = "meeting.participantJoined"
DYTE_EVENT_PARTICIPANT_LEFT = "meeting.participantLeft"
DYTE_EVENT_RECORDING_STATUS_UPDATE = "recording.statusUpdate"

DYTE_MEETING_RECORDING_AWS_PATH = "dyte_webinar_recording_test/"
