from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models
from crater.auctions import constants
from crater.auctions import signals


class Auction(base_models.BaseModel):
    """Base Auction Abstract model class

    Note:
        This is base auction model for auctioning
            anything on the platform.

    """

    # Duration of the auction.
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_closed = models.BooleanField(default=False)

    # This key denotes if bids can be placed on the auction.
    is_active = models.BooleanField(default=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField()
    quantity_sold = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def clean(self):
        if self.quantity_sold > self.quantity:
            raise ValidationError({
                "quantity_sold": _("Quantity exceeds remaining quantity..")
            })

    def update_quantity(self, quantity):
        """Update the quantity sold for an Auction."""
        self.quantity_sold += quantity
        self.save()


class RewardAuction(Auction):
    """Auctions for creator rewards.

    Note:
        This is an auction for a reward, you can place bid
            for a reward purchase, but has to be accepted
            before payment is done. Can't be bought
            directly

    """

    reward = models.ForeignKey(
        "crater_rewards.Reward",
        related_name="auctions",
        on_delete=models.CASCADE
    )

    def __str__(self):
        return "{}".format(self.reward)


class Bid(base_models.BaseModel):
    """Represents a bid placed on an auction or a bid from a user
        to another user for number of coins.

    """

    BID_STATUS_CHOICES = (
        (constants.BID_STATUS_PAYMENT_PENDING_ENUM, constants.BID_STATUS_PAYMENT_PENDING),
        (constants.BID_STATUS_PENDING_ENUM, constants.BID_STATUS_PENDING),
        (constants.BID_STATUS_ACCEPTED_ENUM, constants.BID_STATUS_ACCEPTED),
        (constants.BID_STATUS_REJECTED_ENUM, constants.BID_STATUS_REJECTED),
        (constants.BID_STATUS_CANCELLED_ENUM, constants.BID_STATUS_CANCELLED)
    )

    creator = models.ForeignKey(
        "creator.Creator",
        related_name="bids",
        on_delete=models.CASCADE,
        null=True
    )

    bidder = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )

    # What auction is the bid made for.
    auction = models.ForeignKey(
        RewardAuction,
        null=True,
        blank=True,
        related_name="bids",
        on_delete=models.CASCADE
    )

    # Single coin price.
    bid_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    # What is the status of the bid. Accepted status of bid
    # makes the exchange or coins.
    status = models.PositiveIntegerField(
        choices=BID_STATUS_CHOICES
    )

    # This key tells us if the bid has been processed completely.
    # Note: If this key is false, the bid is invalid.
    is_processed = models.BooleanField(default=False)

    # Attach a payment promise to the Bid.
    payment = models.ForeignKey(
        "crater_payments.Payment",
        related_name="bid",
        on_delete=models.CASCADE,
        null=True
    )

    def __str__(self):
        return "{} - {}".format(self.bidder, self.auction.reward)

    @property
    def amount(self):
        return self.quantity * self.bid_price

    def mark_pending(self):
        """Mark the bid pending."""
        self.status = constants.BID_STATUS_PENDING_ENUM
        self.save()

    def mark_accepted(self):
        """Mark the bid accepted."""
        self.status = constants.BID_STATUS_ACCEPTED_ENUM
        self.save()
        # Send bid accepted signal.
        signals.bid_accepted.send(
            sender=self.__class__,
            bid=self
        )


class CoinPriceLog(base_models.BaseModel):
    """This is the log of the price of a Creator token.

    Note:
        Ideally it'll always be the last accepted bid price.

    """

    coin = models.ForeignKey(
        "creator.Coin",
        related_name="log",
        on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
