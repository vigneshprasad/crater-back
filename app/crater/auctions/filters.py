from django_filters import rest_framework as filters

from crater.auctions import models


class BidsFilters(filters.FilterSet):
    """Custom filter class for Bids."""

    status = filters.MultipleChoiceFilter(
        field_name="status",
        lookup_expr="in",
        conjoined=False,
        choices=models.Bid.BID_STATUS_CHOICES
    )

    class Meta:
        model = models.Bid
        fields = (
            "bidder",
            "auction",
            "status",
            "creator"
        )
