from operator import mod
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.
from base import models as base_models
from crater.sales import constants, signals


class Sale(base_models.BaseModel):
    """This facilitates the sale of a reward directly.

    Note:
        A user can purchase a reward directly if this
            object is created. It is still approved by
            the creator though.

    """
    PAYMENT_TYPE_CHOICES = (
        (constants.SALE_PAYMENT_TYPE_UPI_ENUM, constants.SALE_PAYMENT_TYPE_UPI),
        (constants.SALE_PAYMENT_TYPE_LEARN_ENUM, constants.SALE_PAYMENT_TYPE_LEARN)
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    quantity_sold = models.PositiveIntegerField(default=0)

    # If False, Sale is visible on front end, but can't be bought.
    is_active = models.BooleanField(default=True)
    # Stops the Sale from being show in front end.
    is_closed = models.BooleanField(default=False)

    # Type of payment that can be made for this Sale.
    payment_type = models.PositiveIntegerField(
        default=constants.SALE_PAYMENT_TYPE_LEARN_ENUM,
        choices=PAYMENT_TYPE_CHOICES
    )

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


class RewardSale(Sale):
    """Auctions for creator rewards.

    Note:
        This is an auction for a reward, you can place bid
            for a reward purchase, but has to be accepted
            before payment is done. Can't be bought
            directly

    """

    reward = models.ForeignKey(
        "crater_rewards.Reward",
        related_name="sale",
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "{}".format(self.reward)


class RewardSaleLog(base_models.BaseModel):

    SALE_STATUS_CHOICES = (
        (constants.SALE_PAYMENT_PENDING_ENUM, constants.SALE_PAYMENT_PENDING),
        (constants.SALE_PAYMENT_CONFIRMED_ENUM, constants.SALE_PAYMENT_CONFIRMED),
        (constants.SALE_PAYMENT_DECLINED_ENUM, constants.SALE_PAYMENT_DECLINED)
    )

    PAYMENT_TYPE_CHOICES = (
        (constants.SALE_PAYMENT_TYPE_UPI_ENUM, constants.SALE_PAYMENT_TYPE_UPI),
        (constants.SALE_PAYMENT_TYPE_LEARN_ENUM, constants.SALE_PAYMENT_TYPE_LEARN)
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    reward_sale = models.ForeignKey(
        RewardSale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    # Purchased quantity of a reward.
    quantity = models.PositiveIntegerField()
    # Price paid for the reward (single) buy.
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # What is the status of the bid. Accepted status of bid
    # makes the exchange or coins.
    status = models.PositiveIntegerField(
        default=constants.SALE_PAYMENT_PENDING_ENUM,
        choices=SALE_STATUS_CHOICES
    )

    # If the reward sale log is processed, that means transaction
    # is complete for the reward.
    is_processed = models.BooleanField(default=False)
    payment_type = models.PositiveIntegerField(
        default=constants.SALE_PAYMENT_TYPE_LEARN_ENUM,
        choices=PAYMENT_TYPE_CHOICES
    )
    # Payment object associated with the reward sale.
    payment = models.ForeignKey(
        "crater_payments.Payment",
        related_name="sale_log",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return "{} - {}".format(self.user, self.reward_sale)

    @property
    def amount(self):
        return self.quantity * self.price

    def mark_payment_confirmed(self):
        """Mark the bid accepted."""
        self.status = constants.SALE_PAYMENT_CONFIRMED_ENUM
        self.save()
        # Send bid accepted signal.
        signals.sale_payment_confirmed.send(
            sender=self.__class__,
            sale_log=self
        )
