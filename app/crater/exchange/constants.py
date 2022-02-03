from django.contrib.auth import get_user_model

TRANSACTION_TYPE_BID_ENUM = 1
TRANSACTION_TYPE_REDEMPTION_ENUM = 2
TRANSACTION_TYPE_AUCTION_ENUM = 3

TRANSACTION_TYPE_BID = "Bid"
TRANSACTION_TYPE_REDEMPTION = "Redemption"
TRANSACTION_TYPE_AUCTION = "Auction"


def get_default_crater_user():
    # TODO(Abhishek): Create and Handle Exception
    user = get_user_model().objects.get(email="admin@admin.com")
    return user


