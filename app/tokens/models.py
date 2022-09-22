from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from base import models as base_models
from tokens import constants


class TokenDataPerDay(base_models.BaseModel):
    """Calculates token distribution per day
        for creators eligible for tokens.

    """
    time_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    # Chat message user sent on the stream.
    engagement = models.PositiveIntegerField(default=0)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    date = models.DateField()

    def __str__(self):
        return "{} - {}".format(self.date, self.amount)


class TokenTransaction(base_models.BaseModel):

    USER_TYPE = (
        (constants.USER_TYPE_ATTENDEE_ENUM, constants.USER_TYPE_ATTENDEE),
        (constants.USER_TYPE_STREAMER_ENUM, constants.USER_TYPE_STREAMER)
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    stream = models.ForeignKey(
        "conversations.Group",
        on_delete=models.CASCADE
    )
    # Time spent by the user of the stream.
    time_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    # Chat message user sent on the stream.
    engagement = models.PositiveIntegerField(default=0)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    # Type of transaction log, whether the user streamed,
    # or watched a stream.
    type = models.PositiveSmallIntegerField(
        choices=USER_TYPE,
        default=constants.USER_TYPE_ATTENDEE_ENUM
    )
    date = models.DateField()

    class Meta:
        unique_together = ("user", "stream")

    def __str__(self):
        return "{} - {}".format(self.user, self.stream.id)

    @property
    def creator(self):
        """Returns creator for the host of the group."""
        if not self.stream:
            return ""
        host = self.stream.host
        if not host:
            return ""

        return host.creator if hasattr(host, "creator") else ""


class UserToken(base_models.BaseModel):
    """Token logs user is holding."""

    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    last_updated_at = models.DateTimeField(
        auto_now=True,
        blank=True,
        null=True
    )

    def __str__(self):
        return "{} - {}".format(self.user, self.amount)


class UserTokenLog(base_models.BaseModel):
    """User token log is the log of tokens acquired/redeemed by
        a user.

    """
    TRANSACTION_TYPE = (
        (constants.TRANSACTION_TYPE_ACQUIRED_ENUM, constants.TRANSACTION_TYPE_ACQUIRED),
        (constants.TRANSACTION_TYPE_REDEEMED_ENUM, constants.TRANSACTION_TYPE_REDEEMED)
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="token_logs"
    )
    # Transaction associated with the
    # token log.  In case of redemption it
    # won't be present.
    transaction = models.OneToOneField(
        TokenTransaction,
        on_delete=models.SET_NULL,
        related_name="token_log",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )
    type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE,
        default=constants.TRANSACTION_TYPE_ACQUIRED_ENUM
    )
    date = models.DateField(null=True, blank=True)

    # TODO(Nishant): Add unique here.
    # class Meta:
    #     unique_together = ("user", "transaction", "type")

    def __str__(self):
        return "{} - {} [{}]".format(self.user, self.amount, self.type)
