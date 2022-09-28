from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
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

    # Indicates if the sale should be shown in the store page
    show_in_store = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def clean(self):
        if self.quantity_sold > self.quantity:
            raise ValidationError({
                "quantity_sold": _("Quantity exceeds remaining quantity..")
            })

    def update_quantity(self, quantity):
        """Update the quantity sold for an Sale."""
        self.quantity_sold += quantity
        self.save()

        if self.quantity_sold == self.quantity:
            self.mark_inactive()

    def mark_inactive(self):
        """Marks a reward sale inactive.

        Note:
            If a reward sale is inactive, it can't be bought
                on the platform.

        """
        self.is_active = False
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
    processed_at = models.DateTimeField(null=True, blank=True)

    # What type of payment was made for this reward sale.
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
    # Token log associated with the sale log.
    token_log = models.ForeignKey(
        "tokens.UserTokenLog",
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

    def mark_processed(self):
        """Mark the sale log processed."""
        self.is_processed = True
        if not self.processed_at:
            self.processed_at = timezone.now()

        self.save()

    def mark_sale_confirmed(self):
        """Mark the sale log accepted."""
        self.status = constants.SALE_PAYMENT_CONFIRMED_ENUM
        self.save()

        if not self.processed_at:
            # Send sale accepted signal.
            signals.sale_payment_confirmed.send(
                sender=self.__class__,
                sale_log=self
            )

        self.mark_processed()

    def mark_sale_declined(self):
        """Mark the same log declined."""
        self.status = constants.SALE_PAYMENT_DECLINED_ENUM
        self.save()
        # Send sale declined signal.
        if not self.processed_at:
            # Send sale accepted signal.
            signals.sale_payment_declined.send(
                sender=self.__class__,
                sale_log=self
            )

        self.mark_processed()
