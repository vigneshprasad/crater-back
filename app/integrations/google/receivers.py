from django.dispatch import receiver

from integrations.google import private
from resources.meetings import signals as meeting_signals
from conversations import signals as conversations_signals


@receiver(meeting_signals.meeting_marked_cancelled)
def delete_calendar_event_on_meeting_cancellation(sender, meeting, *args, **kwargs):
    """Remove google calendar event if the meeting is cancelled.

    Args:
        sender(Meeting class): Class representation of meeting.
        meeting(Meeting): Meeting object that was cancelled.

    """
    # Getting distinct event id's for calendar events.
    private.delete_calendar_for_meeting(meeting=meeting)


@receiver(meeting_signals.reschedule_request_created)
def delete_calendar_event_on_meeting_reschedule(sender, reschedule_request, *args, **kwargs):
    """Remove google calendar event if the meeting is cancelled.

    Args:
        sender(Meeting class): Class representation of meeting.
        reschedule_request(RescheduleRequest): Meeting object that was cancelled.

    """
    # Getting distinct event id's for calendar events.
    private.delete_calendar_for_meeting(meeting=reschedule_request.old_meeting)


@receiver(conversations_signals.user_joined_group)
def update_calendar_event_for_user_joining_a_group(sender, user, group, **kwargs):
    """Updates google calendar event when a user joins a group.

    Args:
        sender(Group Class): Group class representation for the group joined.
        user(User): User that joined the group.
        group(Group): Group the user joined into.

    """
    return private.update_or_create_calendar_event_for_conversation(group)


@receiver(conversations_signals.webinar_created)
def create_calendar_event_for_webinar_host(sender, group, *args, **kwargs):
    """Creates google calendar event when an attendee joins a live steam.

    Args:
        sender(Group Class): Group class representation for the group joined.
        group(Group): Group the user joined into.

    """
    return private.create_calendar_event_for_webinar_host(group)


@receiver(conversations_signals.attendee_added_to_group)
def create_calendar_event_for_webinar_attendee(sender, group, user, **kwargs):
    """Creates google calendar event when an attendee joins a live steam.

    Args:
        sender(Group Class): Group class representation for the group joined.
        group(Group): Group the user joined into.
        user(User): User that joined the group.

    """
    return private.create_calendar_event_for_webinar_attendee(user, group)
