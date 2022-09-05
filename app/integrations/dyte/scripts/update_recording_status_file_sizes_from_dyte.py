from integrations.dyte import models, service


def update_status_and_file_sizes(dry_run=True):
    """Update status and fileSize for all Dyte recordings on our end."""
    dyte_recordings = models.DyteMeetingRecording.objects.all()

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
            dyte_recording.save()
            # Update stop and start times.
            dyte_recording.update_start_and_stop_times(started_at, stopped_at)
            total_recordings_updated += 1

        print("************")
