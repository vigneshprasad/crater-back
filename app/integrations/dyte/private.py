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
