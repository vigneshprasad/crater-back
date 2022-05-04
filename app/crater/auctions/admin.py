from django.contrib import admin

from crater.auctions import models


@admin.register(models.RewardAuction)
class RewardAuctionsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reward",
        "start",
        "end",
        "is_closed",
        "base_price",
        "quantity"
    )
    list_editable = ("is_closed", )
    readonly_fields = ("quantity_sold", )
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
    readonly_fields = ("payment", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted",)


@admin.register(models.CoinPriceLog)
class CoinPriceLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "coin",
        "price",
        "created_at"
    )
    exclude = ("deleted_at", "updated_at", "is_deleted")
