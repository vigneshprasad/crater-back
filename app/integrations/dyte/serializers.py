from rest_framework.serializers import ModelSerializer

from integrations.dyte import models


class DyteMeetingSerializer(ModelSerializer):

    class Meta:
        model = models.DyteMeeting
        fields = (
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
            # "is_online",
            "dyte_meeting_detail"
        )


class DyteMeetingRecordingSerializer(ModelSerializer):

    dyte_meeting_detail = DyteMeetingSerializer(source="dyte_meeting")

    class Meta:
        model = models.DyteMeetingRecording
        fields = (
            "pk",
            "dyte_meeting",
            "recording_id",
            "status",
            "path",
            "started_at",
            "stopped_at",
            "dyte_meeting_detail"
        )


class LiveStreamSerializer(ModelSerializer):
    class Meta:
        model = models.LiveStream
        fields = (
            "id",
            "dyte_meeting",
            "status",
            "ingest_seconds",
            "viewer_seconds",
            "ingest_server",
            "livestream_id",
            "playback_url",
            "stream_key",
        )