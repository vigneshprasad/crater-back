import datetime

from integrations.dyte import constants, models, service


def update_status_and_file_sizes(dry_run=True):
    """Update status and fileSize for all Dyte recordings on our end."""
    dyte_recordings = models.DyteMeetingRecording.objects.filter(
        updated_at__lt=datetime.datetime.now(),
        status=constants.DYTE_RECORDING_STATUS_UPLOADED
    )

    print("Total Dyte recordings")
    print(len(dyte_recordings))
    print("----------")

    total_recordings_updated = 0

    for dyte_recording in dyte_recordings:

        recording_data = service.dyte_service.get_recording(
            dyte_recording.dyte_meeting.dyte_meeting_id,
            dyte_recording.recording_id
        )
        if not recording_data:
            continue

        print("Update dyte recording: {}".format(dyte_recording.id))
        try:
            status = recording_data["status"]
            started_at = recording_data["startedTime"]
            stopped_at = recording_data["stoppedTime"]
            file_size = recording_data.get("fileSize") or 0
            file_size_mb = round(file_size/(1024 * 1024), 2)
        except KeyError:
            print("Data not present")
            continue

        print(status)
        print(file_size_mb)
        print(started_at)
        print(stopped_at)

        if not dry_run:
            # Update the status.
            dyte_recording.status = status
            # Update fileSize
            dyte_recording.file_size = file_size_mb

            try:
                dyte_recording.started_at = datetime.datetime.strptime(
                    started_at, constants.DYTE_DATETIME_FORMAT
                ) if started_at else None
                dyte_recording.stopped_at = datetime.datetime.strptime(
                    stopped_at, constants.DYTE_DATETIME_FORMAT
                ) if stopped_at else None
            except ValueError:
                dyte_recording.started_at = None
                dyte_recording.stopped_at = None

            dyte_recording.save()
            total_recordings_updated += 1

        print("************")
