from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
from base import models as base_models
from tokens import models as token_models
from tokens.learn import constants


class LearnDailyTokenAllocation(base_models.BaseModel):
    """Daily allocation of learn."""
    amount = models.PositiveIntegerField(default=1000)
    date = models.DateField()

    def __str__(self):
        return "{} - {}".format(self.date, self.amount)


class LearnToken(base_models.BaseModel):
    """Create each addition to learn token as a log.

    Note:
        Each token acquired/redeemed will be
            recorded. This is how we calculate
            the total tokens a user is holding.

    """

    TRANSACTION_TYPE = (
        (constants.TRANSACTION_TYPE_ACQUIRED_ENUM, constants.TRANSACTION_TYPE_ACQUIRED),
        (constants.TRANSACTION_TYPE_REDEEMED_ENUM, constants.TRANSACTION_TYPE_REDEEMED)
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    # Token log these learn tokens were generated from.
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
        default=constants.TRANSACTION_TYPE_ACQUIRED_ENUM
    )
    date = models.DateField()

    def __str__(self):
        return "{} - {}".format(self.user, self.amount, self.type)
