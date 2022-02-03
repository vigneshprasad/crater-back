from crater.exchange import models
from crater.exchange import constants


def update_or_create_coin_holding_for_buyer(transaction):
    try:
        holding = models.UserCoinHolding.objects.get(
            user=transaction.buyer,
            coin=transaction.coin,
        )
        holding.number_of_coins = holding.number_of_coins + transaction.number_of_coins
        holding.save()

    except models.UserCoinHolding.DoesNotExist:
        holding = models.UserCoinHolding.objects.create(
            user=transaction.buyer,
            coin=transaction.coin,
            number_of_coins=transaction.number_of_coins
        )

    return holding


def update_or_create_coin_holding_for_seller(transaction):
    holding, _ = models.UserCoinHolding.objects.get_or_create(
        user=transaction.seller,
        coin=transaction.coin,
        defaults={
            "number_of_coins": 0,
        }
    )

    number_of_coins_remaining = holding.number_of_coins - transaction.number_of_coins
    if number_of_coins_remaining < 0:
        if not transaction.seller == constants.get_default_crater_user():
            raise Exception

    holding.number_of_coins = holding.number_of_coins - transaction.number_of_coins
    holding.save()
    return holding


def create_transaction_log_for_bid_payment_success(bid, bidder, intent):
    transaction = models.Transaction.objects.create(
        coin=bid.auction.coin,
        number_of_coins=bid.number_of_coins,
        buyer=bidder,
        seller=bid.auction.coin.creator.user,
        payment=bid.payment,
        object_id=bid.id,
        type=constants.TRANSACTION_TYPE_BID_ENUM
    )
    update_or_create_coin_holding_for_buyer(transaction)
    update_or_create_coin_holding_for_seller(transaction)
    return transaction


def update_or_create_transaction_log_for_auction(auction):
    crater_admin = constants.get_default_crater_user()
    transaction, _ = models.Transaction.objects.update_or_create(
        coin=auction.coin,
        buyer=auction.coin.creator.user,
        seller=crater_admin,
        object_id=auction.id,
        type=constants.TRANSACTION_TYPE_AUCTION_ENUM,
        defaults={
            "number_of_coins": auction.number_of_coins
        }
    )
    update_or_create_coin_holding_for_buyer(transaction)
    update_or_create_coin_holding_for_seller(transaction)
