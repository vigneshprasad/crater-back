from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from base import models as base_model
from groups import constants
from resources.meetings import models as meeting_models


class Category(base_model.BaseModel):
    """Top-most level of categorization of group agenda's.

    Example:
        Hiring a CTO, Building a team, Raising seed fund (agendas)
            can all come under Startup Ecosystem category.

    """
    name = models.CharField(max_length=128)
    icon = models.FileField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


class Agenda(base_model.BaseModel):
    """Specific agenda for group's discussion."""
    name = models.CharField(max_length=256)
    icon = models.FileField(blank=True, null=True)
    creator = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="agendas"
    )
    is_approved = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Agenda")
        verbose_name_plural = _("Agendas")

    def __str__(self):
        return "{}-{}".format(self.pk, self.name)

    def save(self, *args, **kwargs):
        # Either user the save override or the to_field and default.
        if not self.creator:
            self.creator = get_user_model().objects.get(email="admin@admin.com")

        super().save(*args, **kwargs)


class Group(base_model.BaseModel):

    GROUP_PRIVACY_CHOICES = (
        (0, constants.GROUP_PRIVACY_PUBLIC),
        (1, constants.GROUP_PRIVACY_PRIVATE)
    )

    GROUP_MEDIUM_CHOICES = (
        (0, constants.GROUP_MEDIUM_AUDIO),
        (1, constants.GROUP_MEDIUM_AUDIO_VIDEO)
    )

    host = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="groups_hosted")
    speakers = models.ManyToManyField(get_user_model(), verbose_name=_("Speakers"), related_name="groups_hosted")
    attendees = models.ManyToManyField(
        get_user_model(),
        verbose_name=_("Attendees"),
        related_name="groups_attended"
    )
    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=True, blank=True)
    interests = models.ManyToManyField(meeting_models.Interest, verbose_name=_("Interests"))
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    max_speakers = models.PositiveIntegerField(default=constants.DEFAULT_MAX_SPEAKERS)
    privacy = models.IntegerField(choices=GROUP_PRIVACY_CHOICES, default=constants.GROUP_PRIVACY_PUBLIC)
    medium = models.IntegerField(choices=GROUP_MEDIUM_CHOICES, default=constants.GROUP_MEDIUM_AUDIO)
    # Group closed status and datetime of closure.
    # TODO(Nishant): Can change this into statuses as well.
    closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")

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
    status = models.IntegerField(choices=INVITE_STATUS_CHOICES, default=constants.INVITE_STATUS_PENDING)
    type = models.IntegerField(choices=INVITE_TYPE_CHOICES, default=constants.INVITE_TYPE_SPEAKER)

    class Meta:
        verbose_name = _("Invite")
        verbose_name_plural = _("Invites")

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
    status = models.IntegerField(choices=REQUEST_STATUS_CHOICES, default=constants.REQUEST_STATUS_PENDING)
    # Will be True for users recommended by WorkNetwork.
    is_recommended = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Request")
        verbose_name_plural = _("Requests")

    def mark_status_as_accepted(self):
        self.status = constants.REQUEST_STATUS_ACCEPTED
        self.save()

    def mark_status_as_declined(self):
        self.status = constants.REQUEST_STATUS_DECLINED
        self.save()
