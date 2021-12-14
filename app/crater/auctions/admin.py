from django.contrib import admin

from crater.auctions import models


@admin.register(models.Auction)
class AuctionsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "coin",
        "start",
        "is_closed",
        "base_price",
        "number_of_coins",
        "coins_sold",
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bidder",
        "auction",
        "bid_price",
        "number_of_coins",
        "status"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.CoinPriceLog)
class CoinPriceLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "coin",
        "price",
        "created_at"
    )
    exclude = ("deleted_at", "updated_at", "is_deleted")
