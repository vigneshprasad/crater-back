from operator import mod
from celery.task import task

from crater.sales import models

@task()
def send_notification_to_creator_for_sale(sale_log_id):
    try:
        sale_log = models.RewardSaleLog.objects.get(id=sale_log_id)

    except models.RewardSaleLog.DoesNotExist:
        return

    creator = sale_log.reward_sale.reward.creator.user
    user = sale_log.user

    # Send notification to Socket io with data