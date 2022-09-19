from tokens import models
from tokens import constants
from tokens.learn import constants as learn_constants


def run(dry_run=True):

    token_transactions = models.TokenTransaction.objects.filter(
        date__gte=learn_constants.LEARN_TOKEN_START_DATE
    )
    user_token_logs = models.UserTokenLog.objects.filter(
        date__gte=learn_constants.LEARN_TOKEN_START_DATE,
        type=constants.TRANSACTION_TYPE_ACQUIRED_ENUM
    )

    print("Token Transactions Count: {}".format(token_transactions.count()))
    print("User Token Log Count: {}".format(user_token_logs.count()))

    print("User Tokens to be deleted: {}".format(user_token_logs.count() - token_transactions.count()))

    total_deleted = 0
    amount_decrease = 0
    creator_tokens = 0
    for token_transaction in token_transactions:
        transaction_token_logs = token_transaction.token_log.all()

        if transaction_token_logs.count() == 1:
            continue

        print("-"*30)
        print(token_transaction.id, token_transaction.amount, token_transaction.date)
        if token_transaction.type == 2:
            creator_tokens += 1

        for transaction_token_log in transaction_token_logs:
            print("*"*10)
            print(transaction_token_log.id, transaction_token_log.amount, transaction_token_log.date)
            if transaction_token_log.date != token_transaction.date:
                print("Deleting transaction token log: {}".format(transaction_token_log.id))
                total_deleted += 1
                amount_decrease += transaction_token_log.amount
                if not dry_run:
                    transaction_token_log.delete(soft=False)
                    print("Hard deleted token log")

    print("Total deleted: {}".format(total_deleted))
    print("Total amount decrease: {}".format(amount_decrease))
    print("Creator tokens: {}".format(creator_tokens))
