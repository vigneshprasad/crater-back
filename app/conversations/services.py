from conversations import models


def get_root_topic(topic):
    """
    Gets root topic or returns None

    Args:
        topic(Topic): the topic for which root needs to be found

    Returns:
        Topic or None

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

