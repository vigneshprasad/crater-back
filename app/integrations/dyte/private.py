from django.core.exceptions import ValidationError

from integrations.dyte import models


def get_dyte_participant_for_user_and_group(user, group):
    """Return dyte meeting participant for a user and group.

    Args:
        user(User): User who is the dyte participant.
        group(Group): Group of which the user should be
            part of.

    """
    dyte_meeting = group.dyte_webinar.first()

    if not dyte_meeting:
        return False

    return user.dyte_participant.filter(
        dyte_meeting=dyte_meeting
    ).first()


def get_dyte_meeting_for_dyte_meeting_id(dyte_meeting_id):
    """Returns dyte meeting for give dyte meeting id.

    Args:
        dyte_meeting_id(str): Dyte meeting on the dyte servers.

    """
    if not dyte_meeting_id:
        return None

    return models.DyteMeeting.objects.filter(
        dyte_meeting_id=dyte_meeting_id
    ).first()


def get_participant_for_user_id_and_dyte_meeting_id(user_pk, dyte_meeting_id):
    """Get Dyte participant for a user and group id.

    Args:
        user_pk(uuid): User pk for which are getting the dyte participant.
        dyte_meeting_id(uuid): Dyte Meeting ID of which the participant is
            a part of.

    """
    if not (user_pk and dyte_meeting_id):
        return None

    try:
        participant = models.DyteMeetingParticipant.objects.get(
            participant_id=user_pk,
            meeting_id=dyte_meeting_id
        ).first()
    except (models.DyteMeetingParticipant.DoesNotExist, ValidationError):
        return None

    return participant


def get_participant_for_user_and_group_id(user, group_id):
    """Get Dyte participant for a user and group id.

    Args:
        user(User): User for which are getting the dyte participant.
        group_id(int): Group ID of which the participant is
            a part of.

    """
    try:
        participant = models.DyteMeetingParticipant.objects.get(
            participant=user,
            dyte_meeting__group_id=group_id
        )
    except models.DyteMeetingParticipant.DoesNotExist:
        return None

    return participant
