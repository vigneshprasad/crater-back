from integrations.dyte import constants
from integrations.dyte import models


def run(dry_run=True):

    recordings = models.DyteMeetingRecording.objects.all()
    for recording in recordings:
        print("-----")
        print(recording.id, recording.status)

    print("-----")

    if not dry_run:
        print("Updating all recordings to uploaded.")
        recordings.update(status=constants.DYTE_RECORDING_STATUS_UPLOADED)
