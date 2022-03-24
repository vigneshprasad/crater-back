import logging

from celery.task import task
import requests
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth import get_user_model

from conversations import constants
from conversations import models
from conversations import signals

User = get_user_model()

LOGGER = logging.getLogger(__name__)


def create_topic(
        title,
        image_name,
        image_url,
        description=None,
        topic_type=constants.GROUP_TYPE_WEBINAR_ENUM
):
    """Creates a topic.

    Args:
        title(str): Name for the topic.
        image_name(str): Name of the image file for the topic.
        image_url(str): Image url from S3 after upload.
        description(str): Description of the topic.
        topic_type(int): Type of topic.

    """
    topic = models.Topic.objects.create(
        name=title,
        type=topic_type,
        description=description
    )

    # Get the image file from the url and save it as
    # image object.
    r = requests.get(image_url)
    image_temp = NamedTemporaryFile()
    image_temp.write(r.content)
    image_temp.flush()

    # This will generate proper image.url as well.
    topic.image.save(image_name, File(image_temp), save=True)

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


def get_all_categories():
    """Returns all active categories."""
    return models.Category.objects.filter(
        is_active=True
    )


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


@task()
def add_attendee_to_group_for_request(attendee_pk, group_request_id):
    """Add user to group as an attendee.

    Args:
        attendee_pk(uuid): PK of attendee to be added to group
        group_request_id(int): Request ID of the group to which user to be added

    """
    try:
        attendee = User.objects.get(pk=attendee_pk)
        group_request = models.Request.objects.get(
            id=group_request_id
        )
    except (User.DoesNotExist, models.Request.DoesNotExist) as e:
        LOGGER.error(str(e))
        return False

    group_request.group.attendees.add(attendee)

    # Send a signal once user is added to the group.
    signals.attendee_added_to_group.send(
        sender=group_request.group.__class__,
        group=group_request.group,
        user=attendee
    )


@task()
def add_attendee_to_series(attendee_pk, series_id, series_request_ids):
    """Add user to series as an attendee.

    Args:
        attendee_pk(uuid): PK of attendee to be added to series.
        series_id(int): ID of series to which attendee needs to be added.
        series_request_ids(list(int)): Series request ids for user.

    """
    try:
        attendee = User.objects.get(pk=attendee_pk)
        series = models.Series.objects.get(
            id=series_id
        )
        series_requests = models.Request.objects.filter(
            id__in=series_request_ids
        )
    except (User.DoesNotExist, models.Series.DoesNotExist) as e:
        LOGGER.error(str(e))
        return False

    # Update request status and add attendee to request group
    for request in series_requests:
        request.group.attendees.add(attendee)

    # Send a signal once user is added to the series.
    signals.attendee_added_to_series.send(
        sender=series.__class__,
        series=series,
        series_requests=series_requests,
        user=attendee
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
        closed=is_closed
    )

    group.speakers.add(*speakers)
    group.categories.add(*categories)

    return group
