import datetime
import json

import numpy as np
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from django.utils import timezone

from conversations import constants
from conversations import exceptions
from conversations import models
from conversations import signals

from crater.creator import models as creator_models

from freelance.settings import REDIS


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

    group_request.status = constants.REQUEST_STATUS_ACCEPTED_ENUM
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

    # Sending group created signal.
    signals.conversation_created.send(
        sender=group.__class__,
        group=group
    )

    return group


def get_groups_attended_for_user(user):
    """Returns groups attended for a user."""
    return models.Group.objects.filter(speakers=user)


def get_groups_for_user(user, queryset=None):
    """ Return list of groups for user filtered based on start time < 30 minutes
        before now and >= user score + 5

    Args:
        user(User): user from the context or request
        queryset(Queryset<Group>): queryset of groups to operate on defaults to all groups.

    Returns:
        Queryset<Group>: queryset of filtered groups for user

    """
    user_score = user.score
    now_time = timezone.now()

    if queryset is None:
        queryset = models.Group.objects.filter(is_approved=True)

    return queryset.filter(
        start__gte=(now_time - datetime.timedelta(days=2)),
        score__lte=(user_score + 5)
    ).order_by("-score", "-start")


def filter_groups_by_score(user, queryset=None):
    """ Return list of groups for user filtered based on >= user score + 5

    Args:
        user(User): user from the context or request
        queryset(Queryset<Group>): queryset of groups to operate on defaults to all groups.

    Returns:
        Queryset<Group>: queryset of filtered groups for user

    """
    user_score = user.score

    if queryset is None:
        queryset = models.Group.objects.filter(is_approved=True)

    return queryset.filter(
        score__lte=(user_score + 5)
    ).order_by("-score", "-start")


def get_distinct_groups_by_score(user, queryset=None):
    """ Return one group per topic for user filtered based
        on group.score >= user score + 5.

    Args:
        user(User): user from the context or request
        queryset(Queryset<Group>): queryset of groups to operate on defaults to all groups.

    Returns:
        Queryset<Group>: queryset of filtered groups for user

    """
    user_score = user.score

    if queryset is None:
        queryset = models.Group.objects.all()

    filtered_queryset = queryset.filter(
        score__lte=(user_score + 5),
        is_full=False
    ).order_by("-score", "start")

    distinct_topics = list(set(filtered_queryset.values_list("topic", flat=True)))
    final_groups = []

    for topic in distinct_topics:
        group = filtered_queryset.filter(topic_id=topic).first()
        if not group:
            continue
        final_groups.append(group)

    # Doing this to return queryset instead of list.
    final_group_ids = [group.id for group in final_groups]
    return models.Group.objects.filter(id__in=final_group_ids)


def get_groups_for_user_and_start(user, start):
    """Return groups for a user scheduled at the given start
        time.

    Args:
        user(User): Group host or speaker.
        start(datetime.datetime): Start datetime for the
            groups.

    """
    return models.Group.objects.filter(
        Q(host=user) | Q(speakers=user),
        start=start
    ) or None


def get_request_for_user_and_group_id(
        user,
        group_id,
        participant_type=constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM
):
    """Return a Request for given user and group_id.

    Args:
        user(User): User who has requested to join the group.
        group_id(int): ID of group to for which we are getting
            the request for.
        participant_type(int): Participant type the user requested
            for.

    """
    return models.Request.objects.filter(
        requester=user,
        group_id=group_id,
        participant_type=participant_type
    ).last()


def add_attendee_to_group_for_request(attendee, group_request):
    """Add speaker to group as an attendee and raise exception if conditions not met

    Args:
        attendee(User): Attendee to be added to group
        group_request(Request): Request to the group to which user to be added

    Returns:
        group_request(Request): Group request

    """

    group_request.status = constants.REQUEST_STATUS_ACCEPTED_ENUM
    group_request.group.attendees.add(attendee)
    group_request.save()

    # Send a signal once user is added to the group.
    signals.attendee_added_to_group.send(
        sender=group_request.group.__class__,
        group=group_request.group,
        user=attendee
    )

    return group_request


def get_or_create_topic(name, image, description, creator):
    """Return a topic for the provided args.

    Args:
        name(str): Name of the topic.
        image(file): Image associated with the topic.
        description(str): Description of the topic
        creator(Creator): Creator who created the topic.

    """
    topic, _ = models.Topic.objects.get_or_create(
        name=name,
        description=description,
        creator=creator,
        defaults={"image": image}
    )

    return topic


def participant_count(limit, current, sec):
    """Calculates participant count based on the
        current count and seconds into the session.

    Args:
        limit(int): Max count for participants.
        current(int): Current participant count.
        sec(int): Number of seconds into the session.

    """
    if not limit:
        return 0, 0

    rate_of_change = min(limit / 5, 1500)
    limit = limit / 100 if limit else 100
    sec += 10

    # Make the final count and current count same.
    final = current

    # Calculate probability for participant going up or down.
    random = np.random.rand()
    random_2 = np.random.rand()
    prob = max(0.6, (1 - (sec / rate_of_change)))
    neg_prob = min(0.6, (sec * 2 / rate_of_change))

    # Update the final count of participants based on the probability.
    if sec > 1800:
        final += np.random.randint(1, 2) if random_2 <= prob else 0
        final -= np.random.randint(1, 3) if random <= neg_prob else 0
    elif (sec // 300) % 2 == 1:
        final += np.random.randint(1, 3) if random_2 <= prob else 0
        final -= np.random.randint(1, 3) if random <= neg_prob else 0
    else:
        final += np.random.randint(1, 8) if random_2 <= prob else 0
        final -= np.random.randint(1, 6) if random <= neg_prob else 0

    # Calculate new final participant count and current seconds.
    final, sec = (current, sec) if (
            final < 1 or final > limit
    ) else (final, sec)

    return final, sec


def cache_live_webinar(group):
    """Cache live webinar to redis

    Args:
        group(Group): Group instance with type webinar

    """
    try:
        creator = creator_models.Creator.objects.get(user=group.host)
    except creator_models.Creator.DoesNotExist:
        return False

    # Data to be cached to Redis for the group.
    data_to_cache_for_group = {
        "group_id": group.id,
        "participant": creator.participant_count or creator.number_of_subscribers
    }

    cached_live_webinars = REDIS.get("live_webinars")
    live_webinars = json.loads(cached_live_webinars.decode("ascii")).get(
        "webinars",
        []
    ) if cached_live_webinars else []

    # Generate list of all group ids in the cache.
    group_ids = [webinar.get("group_id") for webinar in live_webinars]

    # If the Group Id is already present in cached group
    # ids, return.
    if group.id in group_ids:
        return True

    live_webinars.append(data_to_cache_for_group)
    REDIS.set(
        "live_webinars",
        json.dumps({
            "webinars": live_webinars
        })
    )

    return True


def remove_cached_live_webinar(group):
    """Remove cached live webinar from redis

    Args:
        group(Group): Group instance with type webinar

    """
    # Check if live webinars are cached
    cached_live_webinars = REDIS.get("live_webinars")
    if not cached_live_webinars:
        return True

    live_webinars = json.loads(cached_live_webinars.decode("ascii")).get("webinars")
    group_data = None

    for data in live_webinars:
        if data.get("group_id") == group.id:
            group_data = data

    # If there is not data related to the group
    # in the cache, return.
    if not group_data:
        return True

    # Remove the group data from the live webinars.
    live_webinars.remove(group_data)

    REDIS.set(
        "live_webinars",
        json.dumps({"webinars": live_webinars})
    ) if live_webinars else REDIS.delete("live_webinars")

    cached_webinar_count = REDIS.get(f"{group.id}")
    if not cached_webinar_count:
        return True

    # Delete the group count from REDIS.
    REDIS.delete(f"{group.id}")

    # Send live count as 0 to channel layer group
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"{group.id}",
        {
            "type": "send.live_count",
            "text": json.dumps(
                {
                    "type": "live_count",
                    "count": 0
                }
            )
        }
    )
