from django.contrib import admin

from crater.auctions import models


@admin.register(models.RewardAuction)
class RewardAuctionsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reward",
        "start",
        "is_closed",
        "is_active",
        "base_price",
        "quantity",
        "quantity_sold"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bidder",
        "auction",
        "bid_price",
        "quantity",
        "status"
    )
    raw_id_fields = ("bidder", "creator")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted", "payment")


@admin.register(models.CoinPriceLog)
class CoinPriceLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "coin",
        "price",
        "created_at"
    )
    exclude = ("deleted_at", "updated_at", "is_deleted")
