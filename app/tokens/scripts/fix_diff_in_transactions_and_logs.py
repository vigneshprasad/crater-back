from django.db.models import Sum

from tokens import models


def run(date, dry_run=True):
    print(date)
    token_transactions = models.TokenTransaction.objects.filter(date=date)
    transaction_amount = token_transactions.aggregate(total_amount=Sum("amount"))["total_amount"] or 0
    user_token_logs = models.UserTokenLog.objects.filter(date=date, type=1)
    log_amount = user_token_logs.aggregate(total_amount=Sum("amount"))["total_amount"] or 0
    diff = transaction_amount - log_amount

    print(transaction_amount)
    print(log_amount)
    print("Total diff")
    print(diff)

    for user_token_log in user_token_logs:
        transaction = user_token_log.transaction
        token_transactions = token_transactions.exclude(id=transaction.id)
        if transaction.amount == user_token_log.amount:
            continue

        print(transaction.id, transaction.amount)
        print(user_token_log.id, user_token_log.amount)
        print("Diff")
        print(transaction.amount - user_token_log.amount)
        transaction.save()
        print("*"*30)

    # print(token_transactions)
    print("-"*30)
