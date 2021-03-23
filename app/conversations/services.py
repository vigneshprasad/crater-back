from conversations import models


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


def update_request_and_add_user_to_group(user, group_request):
    """ Add user to group and update the request status

    Args:
        user(User): user object to be added to group
        group_request(Request): reference to group object user is added to

    Returns:
        request(Request): group request object
    """
    group_request.status = models.Request.REQUEST_STATUS_CHOICES[1][0]
    group_request.group.speakers.add(user)
    group_request.save()
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
