import datetime

from django.utils import timezone

from conversations import exceptions
from conversations import models
from conversations import signals


def get_root_topic(topic):
    """Gets root topic for given topic.

    Args:
        topic(Topic): the topic for which root needs to be found

    Returns:
        Root Topic or None if no root topic available.

    """
    root = topic
    while root.parent is not None:
        root = topic.parent

    if root == topic:
        return None
    return root


def add_speaker_to_group_for_request(speaker, group_request):
    """Add speaker to group and raise exception if conditions not met

    Args:
        speaker(User): speaker to be added to group
        group_request(Request): request to the group to which user to be added

    Returns:
        group(Group): group with speaker added

    """
    group = group_request.group
    current_members_count = len(group.speakers.all())

    if current_members_count >= group.max_speakers:
        raise exceptions.GroupMaxSpeakersException()

    # If the user is already part of the group at the same time. Don't allow.
    if models.Group.objects.filter(start=group.start, speakers=speaker):
        raise exceptions.GroupJoinedAtTheSameTime()

    group_request.status = models.Request.REQUEST_STATUS_CHOICES[1][0]
    group_request.group.speakers.add(speaker)
    group_request.save()

    # Sending a signal when user joins a group successfully.
    signals.user_joined_group.send(
        sender=group.__class__,
        user=speaker,
        group=group
    )

    return group_request


def create_group_conversation(users, interests, topic, start, end):
    """Create group.

    Args:
        users(list): List of users that should be part of the group.
        interests(list): List of interest for the group.
        topic(Topic): Topic of the group.
        start(datetime.datetime): Start datetime for the group conversation.
        end(datetime.datetime): End datetime for the group conversation.

    Returns:
        Created Group object.

    """
    group = models.Group.objects.create(
        topic=topic,
        start=start,
        end=end
    )
    # Adding speakers for the group.
    for user in users:
        group.speakers.add(user)
    # Adding interests to the group.
    for interest in interests:
        group.interests.add(interest)

    # Refreshing for updated values.
    group.refresh_from_db()

    return group


def get_groups_attended_for_user(user):
    """Returns groups attended for a user."""
    return models.Group.objects.filter(speakers=user)

    
def get_groups_for_user(user, queryset=None):
    """ Return list of groups for user filtered based on start time < 30 mins before now
    and >= user score + 5

    Args:
        user(User): user from the context or request
        queryset(Queryset<Group>): queryset of groups to operate on defaults to all groups
        not closed.

    Returns:
        Queryset<Group>: queryset of filtered groups for user

    """
    user_score = user.score
    now_time = timezone.now()

    if not queryset:
        queryset = models.Group.objects.filter(closed=False)

    return queryset.filter(
        start__gte=(now_time - datetime.timedelta(days=2)),
        score__lte=(user_score + 5)
    ).order_by("-score", "-start")
