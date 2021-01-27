from groups import constants
from groups import models


def can_respond_to_requests(user, request):
    """Returns true if the user can accept invites for a group."""
    group = request.group
    if user.pk != group.host.pk:
        return False
    return True


def update_group_on_invite_acceptance(invite):
    """Updates the group if someone accepts the group invite."""
    invitee = invite.invitee
    group = invite.group

    if invite.type == constants.INVITE_TYPE_SPEAKER:
        request, _ = models.Request.objects.get_or_create(
            requester=invitee,
            group=group
        )
    elif invite.type == constants.INVITE_TYPE_ATTENDEE:
        if group.privacy == constants.GROUP_PRIVACY_PRIVATE:
            return
        group.attendees.add(invitee)


def update_group_on_request_acceptance(request):
    """Updates the group if a group request is accepted."""
    group = request.group
    if not group.can_add_speakers():
        return
    group.speakers.add(request.requester)
