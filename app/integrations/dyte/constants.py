from django.conf import settings

DYTE_ORG_ID = settings.DYTE_ORD_ID
DYTE_APP_ID = settings.DYTE_APP_ID

DYTE_PROD_BASE_URL = settings.DYTE_PROD_BASE_URL
DYTE_JOIN_MEETING_BASE_URL = settings.DYTE_JOIN_MEETING_BASE_URL
DYTE_BASE_URL_V2 = "https://api.cluster.dyte.in/v2"

# Dyte present constants.
DEFAULT_PRESET_NAME = "participant"
DEFAULT_WEBINAR_PRESET_NAME = "webinar_view_preset"

# Default participant and host presets.
DEFAULT_WEBINAR_PARTICIPANT_PRESET_NAME = "webinar_participant"
DEFAULT_WEBINAR_HOST_PRESET_NAME = "default_webinar_host_preset"

# OBS presets.
WEBINAR_OBS_HOST_PRESET_NAME = "default_webinar_host_preset_obs"
WEBINAR_OBS_PARTICIPANT_PRESET_NAME = "webinar_participant_obs"

# Dyte webhook events.
DYTE_EVENT_MEETING_STARTED = "meeting.started"
DYTE_EVENT_MEETING_ENDED = "meeting.ended"
DYTE_EVENT_PARTICIPANT_JOINED = "meeting.participantJoined"
DYTE_EVENT_PARTICIPANT_LEFT = "meeting.participantLeft"
DYTE_EVENT_RECORDING_STATUS_UPDATE = "recording.statusUpdate"
DYTE_EVENT_LIVESTREAM_STATUS_UPDATE = "livestreaming.statusUpdate"

# Dyte recording status.
DYTE_RECORDING_STATUS_INVOKED = "INVOKED"
DYTE_RECORDING_STATUS_RECORDING = "RECORDING"
DYTE_RECORDING_STATUS_UPLOADING = "UPLOADING"
DYTE_RECORDING_STATUS_UPLOADED = "UPLOADED"
DYTE_RECORDING_STATUS_ERRORED = "ERRORED"

DYTE_MEETING_RECORDING_AWS_PATH = "dyte_webinar_recording/{group_id}/"


LIVE_STREAM_STATUS_OFFLINE = "OFFLINE"
LIVE_STREAM_STATUS_LIVE = "LIVE"
