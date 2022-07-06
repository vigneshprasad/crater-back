from django.contrib.auth import get_user_model
from django.db import models

from base import models as base_models


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
    tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    date = models.DateField(auto_now_add=True)


class TokenLogDataPerUser(base_models.BaseModel):

    TRANSACTION_TYPE = (
        (1, "Attendee"),
        (2, "Streamer")
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
    tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    # Type of transaction log, whether the user streamed,
    # or watched a stream.
    type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE,
        default=TRANSACTION_TYPE[0][0]
    )


class UserTokenHolding(base_models.BaseModel):

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    learn_tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )


class UserTokenHoldingLog(base_models.BaseModel):
    """Create each addition to token as a log.

    Note:
        Each token acquired/redeemed will be
            recorded. This is how we calculate
            the total tokens a user is holding.

    """

    TRANSACTION_TYPE = (
        (1, "Acquired"),
        (2, "Redeemed")
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    learn_tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE,
        default=TRANSACTION_TYPE[0][0]
    )
