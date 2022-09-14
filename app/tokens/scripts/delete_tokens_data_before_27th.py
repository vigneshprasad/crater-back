from tokens import models
from tokens.learn import constants as learn_constants


def run(dry_run=True):
    user_token_logs = models.UserToken.objects.filter(date__lt=learn_constants.LEARN_TOKEN_START_DATE)
    token_transactions = models.TokenTransaction.objects.filter(date__lt=learn_constants.LEARN_TOKEN_START_DATE)
    token_data_per_day = models.TokenDataPerDay.objects.filter(date__lt=learn_constants.LEARN_TOKEN_START_DATE)

    dates = list(token_data_per_day.values_list("date", flat=True))
    print("Deleting data for dates: {}".format(dates))

    for date in dates:
        print("-"*10)
        print(date)
        print("User Token Logs: {}".format(user_token_logs.filter(date=date).count()))
        print("Token Transaction: {}".format(token_transactions.filter(date=date).count()))
        print("Token Data Per Day: {}".format(token_data_per_day.filter(date=date).count()))

    if not dry_run:
        print("Hard deleting objects")
        print("User Token Logs Deleted: {}".format(user_token_logs.delete(soft=False)))
        print("Token Transactions Deleted: {}".format(token_transactions.delete(soft=False)))
        print("Token Data Per Day Deleted: {}".format(token_data_per_day.delete(soft=False)))
