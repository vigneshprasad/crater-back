from resources.meetings import models


def run(dry_run=True):

    meeting_preferences = models.MeetingPreference.objects.all()

    for meeting_preference in meeting_preferences:
        print("Start", "-"*30)
        print("Preference: {}".format(meeting_preference.id))
        first_time_slot = meeting_preference.time_slots.first()

        if not first_time_slot:
            print("No Time Slot found: {}".format(meeting_preference.id))
            continue

        print("Time Slot for preference: {}".format(first_time_slot.get_display()))

        if not dry_run:
            # Remove all time slots.
            print("Removing all time slots for preference")
            meeting_preference.time_slots.clear()
            # Append only the single time slot.
            print("Added time slot for preference: {}".format(first_time_slot.get_display()))
            meeting_preference.time_slots.add(first_time_slot)

        print("End", "-" * 30)
