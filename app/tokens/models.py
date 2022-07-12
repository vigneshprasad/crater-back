from django.contrib.auth import get_user_model
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
    # Creator for which the points were earned
    # from.
    creator = models.ForeignKey(
        "creator.Creator",
        on_delete=models.CASCADE,
        null=True,
        blank=True
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


class UserTokenLog(base_models.BaseModel):

    # Whether the token was acquired or redeemed.
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
    transaction = models.ForeignKey(
        TokenTransaction,
        on_delete=models.CASCADE,
        related_name="token_log",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE,
        default=constants.TRANSACTION_TYPE_ACQUIRED_ENUM
    )
    date = models.DateField()

    def __str__(self):
        return "{} - {} [{}]".format(self.user, self.amount, self.type)
