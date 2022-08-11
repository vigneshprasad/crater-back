from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.
from base import models as base_models


class Sale(base_models.BaseModel):
    """This facilitates the sale of a reward directly.

    Note:
        A user can purchase a reward directly if this
            object is created. It is still approved by
            the creator though.

    """
    price = models.DecimalField(max_digits=10, decimal_places=2)
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
        related_name="auctions",
        on_delete=models.CASCADE
    )

    def __str__(self):
        return "{}".format(self.reward)


class RewardSaleLog(base_models.BaseModel):
    pass
