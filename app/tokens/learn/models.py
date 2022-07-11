from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
from base import models as base_models
from tokens import models as token_models


class LearnDailyTokenAllocation(base_models.BaseModel):
    """Daily allocation of learn."""
    learn = models.PositiveIntegerField()
    date = models.DateField()


class LearnToken(base_models.BaseModel):
    """Create each addition to learn token as a log.

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
    # Token log this learn tokens were generated from.
    token_log = models.ForeignKey(
        token_models.UserTokenLog,
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE,
        default=TRANSACTION_TYPE[0][0]
    )
