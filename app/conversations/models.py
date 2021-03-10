from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from base import models as base_model
from conversations import constants
from resources.meetings import models as meeting_models


class Topic(base_model.BaseModel):
    """Topic of discussion for a conversation.

    It has self-reference of the {parent} topic to create nesting.

    Example:
        (Topic) How to buid a brand?, a topic (Topic)  Marketing can be pareent
        to create nesting

    """
    name = models.CharField(max_length=128)
    image = models.ImageField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey(
        'conversations.Topic',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    is_approved = models.BooleanField(default=True)
    description = models.TextField(max_length=255, null=True, blank=True)
    creator = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Topic")
        verbose_name_plural = _("Topics")

    def __str__(self):
        return "{}-{}".format(self.pk, self.name)


class Group(base_model.BaseModel):

    GROUP_PRIVACY_CHOICES = (
        (0, constants.GROUP_PRIVACY_PUBLIC),
        (1, constants.GROUP_PRIVACY_PRIVATE)
    )

    GROUP_MEDIUM_CHOICES = (
        (0, constants.GROUP_MEDIUM_AUDIO),
        (1, constants.GROUP_MEDIUM_AUDIO_VIDEO)
    )

    host = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="groups_hosted", null=True, blank=True)
    speakers = models.ManyToManyField(get_user_model(), verbose_name=_("Speakers"), related_name="groups_speaker")
    attendees = models.ManyToManyField(
        get_user_model(),
        verbose_name=_("Attendees"),
        related_name="groups_attended",
        blank=True,
    )
    topic = models.ForeignKey('conversations.Topic', on_delete=models.CASCADE, related_name="group")
    description = models.TextField(max_length=1024, null=True, blank=True)
    interests = models.ManyToManyField(meeting_models.Interest, verbose_name=_("Interests"))
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    max_speakers = models.PositiveIntegerField(default=constants.DEFAULT_MAX_SPEAKERS)
    privacy = models.IntegerField(choices=GROUP_PRIVACY_CHOICES, default=GROUP_PRIVACY_CHOICES[0][0])
    medium = models.IntegerField(choices=GROUP_MEDIUM_CHOICES, default=GROUP_MEDIUM_CHOICES[0][0])
    # Group closed status and datetime of closure.
    # TODO(Nishant): Can change this into statuses as well.
    closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")

    def __str__(self):
        return "{}-{}-{}".format(self.pk, self.topic, self.host)

    def can_add_speakers(self):
        """Return True if speakers can be added to the group."""
        if self.speakers.count() > self.max_speakers:
            return False
        return True


class Invite(base_model.BaseModel):

    INVITE_STATUS_CHOICES = (
        (0, constants.INVITE_STATUS_PENDING),
        (1, constants.INVITE_STATUS_ACCEPTED),
        (2, constants.INVITE_STATUS_DECLINED)
    )

    INVITE_TYPE_CHOICES = (
        (0, constants.INVITE_TYPE_SPEAKER),
        (1, constants.INVITE_TYPE_ATTENDEE)
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="invites")
    inviter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="group_invites_created")
    invitee = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="groups_invites_received",
        null=True,
        blank=True
    )
    invitee_email = models.EmailField(max_length=128, null=True, blank=True)
    status = models.IntegerField(choices=INVITE_STATUS_CHOICES, default=INVITE_STATUS_CHOICES[0][0])
    type = models.IntegerField(choices=INVITE_TYPE_CHOICES, default=INVITE_TYPE_CHOICES[0][0])

    class Meta:
        verbose_name = _("Invite")
        verbose_name_plural = _("Invites")

    def __str__(self):
        return "{}-{}-{}".format(self.pk, self.group_id, self.invitee)

    def mark_status_as_accepted(self):
        self.status = constants.INVITE_STATUS_ACCEPTED
        self.save()

    def mark_status_as_declined(self):
        self.status = constants.INVITE_STATUS_DECLINED
        self.save()


class Request(base_model.BaseModel):

    REQUEST_STATUS_CHOICES = (
        (0, constants.REQUEST_STATUS_PENDING),
        (1, constants.REQUEST_STATUS_ACCEPTED),
        (2, constants.REQUEST_STATUS_DECLINED)
    )

    requester = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="group_requests")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="requests")
    status = models.IntegerField(choices=REQUEST_STATUS_CHOICES, default=REQUEST_STATUS_CHOICES[0][0])
    # Will be True for users recommended by WorkNetwork.
    is_recommended = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Request")
        verbose_name_plural = _("Requests")

    def __str__(self):
        return "{}-{}-{}".format(self.pk, self.group_id, self.requester)

    def mark_status_as_accepted(self):
        self.status = constants.REQUEST_STATUS_ACCEPTED
        self.save()

    def mark_status_as_declined(self):
        self.status = constants.REQUEST_STATUS_DECLINED
        self.save()