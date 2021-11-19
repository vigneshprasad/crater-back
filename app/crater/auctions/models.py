from django.db import models

# Create your models here.
from base import models as base_models
from crater.auctions import constants


class Auction(base_models.BaseModel):
    coin = models.ForeignKey(
        "creator.Coin",
        related_name="auctions",
        on_delete=models.CASCADE
    )
    # Duration of the auction.
    start = models.DateTimeField()
    end = models.DateTimeField()

    # Should be the same as end. Discuss with Vignesh.
    expires_at = models.DateTimeField()

    base_price = models.PositiveIntegerField()
    number_of_coins = models.PositiveIntegerField()
    coins_sold = models.PositiveIntegerField()


class Bid(base_models.BaseModel):
    """Represents a bid placed on an auction or a bid from a user
        to another user for number of coins.

    """
    # TODO(Nishant): Think of how a bid from one user to another will work.

    BID_STATUS_CHOICES = (
        (constants.BID_STATUS_ACCEPTED_ENUM, constants.BID_STATUS_ACCEPTED),
        (constants.BID_STATUS_REJECTED_ENUM, constants.BID_STATUS_REJECTED),
        (constants.BID_STATUS_CANCELLED_ENUM, constants.BID_STATUS_CANCELLED)
    )

    auction = models.ForeignKey(
        Auction,
        related_name="bids",
        on_delete=models.CASCADE
    )

    bid_price = models.DecimalField()
    number_of_coins = models.PositiveIntegerField()
    bid_at = models.DateTimeField()

    status = models.PositiveIntegerField(
        choices=BID_STATUS_CHOICES
    )

    # Attach a payment promise to the Bid.
    # payment = models.ForeignKey()


class CoinPriceLog(base_models.BaseModel):
    """This is the log of the price of a Creator token.

    Note:
        Ideally it'll always be the last accepted bid price.

    """
    coin = models.ForeignKey(
        "creator.Coin",
        related_name="auctions",
        on_delete=models.CASCADE
    )
    price = models.PositiveIntegerField()

    # TODO(Nishant): Should we keep a bid object here?
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)
