from conversations import constants
from conversations import models


def create_topic(
        title,
        image,
        description=None,
        created_by=None,
        topic_type=constants.GROUP_TYPE_WEBINAR_ENUM
):
    """Creates a topic.

    Args:
        title(str): Name for the topic.
        image(file): Image file for the topic.
        description(str): Description of the topic.
        created_by(User): User who is creating the topic.
        topic_type(int): Type of topic.

    """
    topic = models.Topic.objects.create(
        name=title,
        imgae=image,
        type=topic_type,
        description=description,
        creator=created_by
    )
    return topic


def get_topic(topic_id):
    """Returns a topic object for a topic ID.

    Args:
        topic_id(int): ID of the topic object.

    """
    try:
        topic = models.Topic.objects.get(id=topic_id)
    except models.Topic.DoesNotExist:
        return None

    return topic


def get_category_for_id(category_id):
    """Returns a category object for a category ID.

    Args:
        category_id(int): ID of the category object.

    """
    try:
        category = models.Category.objects.get(
            id=category_id
        )
    except models.Category.DoesNotExist:
        return None

    return category


def get_all_categories():
    """Returns all active categories."""
    return models.Category.objects.filter(
        is_active=True
    )


def create_webinar(
        host,
        speakers,
        topic,
        description,
        start,
        categories,
        group_type=constants.GROUP_TYPE_WEBINAR_ENUM,
        is_featured=False,
        is_closed=False,
        is_published=False
):
    """Creates a group based on provided args.

    Args:
        host(User): Host of the group.
        speakers(queryset(User)): Speakers of the group.
        topic(Topic): Topic of the group.
        description(str): Description of the group.
        start(start): Start datetime of the group.
        categories(queryset(Category)): Categories of the group.
        group_type(int): Type of group.
        is_featured(bool): Should the group be featured.
        is_closed(bool): Is the group active or inactive.
        is_published(bool): Should we show the group on website.

    """
    group = models.Group.objects.create(
        topic=topic,
        host=host,
        start=start,
        description=description,
        type=group_type,
        is_featured=is_featured,
        is_published=is_published,
        is_closed=is_closed
    )

    group.speakers.add(*speakers)
    group.categories.add(*categories)

    return group
