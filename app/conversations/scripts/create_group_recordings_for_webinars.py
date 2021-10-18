import datetime

from conversations import models
from conversations import constants
from integrations.dyte import models as dyte_models


def run(dry_run=True):

    old_webinars = models.Group.objects.filter(
        type=constants.GROUP_TYPE_WEBINAR_ENUM,
        start__lt=datetime.datetime.now()
    )

    for webinar in old_webinars:

        print(webinar.id)
        print(webinar.host)
        print(webinar.type)

        dyte_recordings = []
        dyte_meeting = webinar.dyte_webinar.first()
        if dyte_meeting:
            dyte_recordings = dyte_models.DyteMeetingRecording.objects.filter(
                dyte_meeting=dyte_meeting
            )

        if not dry_run:
            group_recording, _ = models.GroupRecording.objects.get_or_create(
                group=webinar
            )

            for dyte_recording in dyte_recordings:
                group_recording.dyte_recordings.add(dyte_recording)

        print("-----")
