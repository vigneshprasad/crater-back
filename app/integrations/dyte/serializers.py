from rest_framework.serializers import ModelSerializer

from integrations.dyte import models


class DyteMeetingSerializer(ModelSerializer):
    class Meta:
        model = models.DyteMeeting
        fields = (
            "meeting",
            "group",
            "dyte_meeting_id",
            "room_name"
        )


class DyteParticipantSerializer(ModelSerializer):
    dyte_meeting_detail = DyteMeetingSerializer(source="dyte_meeting")

    class Meta:
        model = models.DyteMeetingParticipant
        fields = (
            "pk",
            "dyte_meeting",
            "auth_token",
            "is_online",
            "dyte_meeting_detail"
        )


class DyteMeetingRecordingSerializer(ModelSerializer):
    dyte_meeting_detail = DyteMeetingSerializer(source="dyte_meeting")

    class Meta:
        model = models.DyteMeetingMeetingRecording
        fields = (
            "pk",
            "dyte_meeting",
            "recording_id",
            "status",
            "path",
            "started_at",
            "stopped_at"
        )
