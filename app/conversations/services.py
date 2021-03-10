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