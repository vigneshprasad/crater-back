import datetime

from celery.schedules import crontab
from celery.task import periodic_task, task

from tokens import models as token_models, constants as token_constants
from tokens.learn import models, constants


@periodic_task(run_every=crontab(hour=19, minute=15))
def create_daily_allocation_for_learn():
    """Creates daily allocation for learn tokens.

    Note:
        Creating a model so that it can be edited, and we
            can allocate different amount.

    """
    models.LearnDailyTokenAllocation.objects.create(date=datetime.date.today())


@task()
def calculate_learn_tokens_earned(date):
    """Calculate learn tokens for the date provided.

    Args:
        date(Date): Date for which we are calculating learn
            tokens for users.

    """
    user_token_logs = token_models.UserTokenLog.objects.filter(
        date=date,
        type=token_constants.TRANSACTION_TYPE_ACQUIRED_ENUM
    )
    user_ids = user_token_logs.values_list("user", flat=True)
    unique_user_ids = list(set(user_ids))

    token_data_for_date = token_models.TokenDataPerDay.objects.filter(
        date=date
    ).first()
    if not token_data_for_date:
        return

    total_calculation_date = token_data_for_date.time_spent + (2 * token_data_for_date.engagement)
    daily_token_allocation = models.LearnDailyTokenAllocation.objects.filter(date=date).first()
    if not daily_token_allocation:
        return

    for user_id in unique_user_ids:
        token_logs = user_token_logs.filter(user_id=user_id)
        total_redeemed_amount = 0

        for token_log in token_logs:
            transaction = token_log.transaction
            learn_token = models.LearnToken.objects.create(
                user=token_log.user,
                token_log=token_log,
                date=date,
                type=constants.TRANSACTION_TYPE_ACQUIRED_ENUM
            )
            # Calculate learn amount based on the type of user.
            if transaction.type == token_constants.USER_TYPE_ATTENDEE_ENUM:
                user_total = transaction.time_spent + (2 * transaction.engagement)
                learn_token.amount = user_total/total_calculation_date * 0.8 * daily_token_allocation.amount
                learn_token.save()
            elif transaction.type == token_constants.USER_TYPE_STREAMER_ENUM:
                user_total = transaction.time_spent + (2 * transaction.engagement)
                learn_token.amount = user_total / total_calculation_date * 0.2 * daily_token_allocation.amount
                learn_token.save()

            # Update the redeemed amount.
            total_redeemed_amount += token_log.amount

        # Mark all tokens converted to Learn as redeemed.
        token_models.UserTokenLog.objects.create(
            user_id=user_id,
            amount=total_redeemed_amount,
            date=date,
            type=token_constants.TRANSACTION_TYPE_REDEEMED_ENUM
        )
