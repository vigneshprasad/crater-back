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


def add_user_to_group(user, group_id):
    """ Add user to group check if condition match
    Args:
        user(User): user object to be added to group
        group(Group): reference to group object user is added to

    """
    try:
        group = models.Group.objects.get(pk=group_id)
        
    except models.Group.DoesNotExist:
        raise models.Group.DoesNotExist
