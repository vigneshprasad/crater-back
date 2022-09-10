import json

from celery.task import task
from rest_framework.renderers import JSONRenderer

from crater.sales import models, serializers
from utils.socket_io_service import socket_io_service


@task()
def send_notification_to_creator_for_sale(sale_log_id):
    """Send web/mobile notification to creator when a user
        purchases a reward.

    Args:
        sale_log_id(int): ID of the sale that was created.

    """
    try:
        sale_log = models.RewardSaleLog.objects.get(id=sale_log_id)
    except models.RewardSaleLog.DoesNotExist:
        return False

    creator = sale_log.reward_sale.reward.creator.user
    # Send notification to Socket io with data
    serialized = serializers.RewardSaleLogSerializer(sale_log).data
    data = json.loads(JSONRenderer().render(serialized).decode("utf8"))
    socket_io_service.post_notification_user(data, str(creator.pk), "creator-sale-request")


@task()
def send_notification_user_sale_accepted(sale_log_id):
    """Sends web/mobile notification to a user when a sale is accepted
        by the creator.

    Args:
        sale_log_id(int): ID of the sale that was accepted.

    """
    try:
        sale_log = models.RewardSaleLog.objects.get(id=sale_log_id)
    except models.RewardSaleLog.DoesNotExist:
        return False

    user = sale_log.user
    # Send notification to Socket io with data
    serialized = serializers.RewardSaleLogSerializer(sale_log).data
    data = json.loads(JSONRenderer().render(serialized).decode("utf8"))
    socket_io_service.post_notification_user(data, str(user.pk), "creator-sale-accepted")


@task()
def send_notification_user_sale_declined(sale_log_id):
    """Sends web/mobile notification to a user when a sale is declined
        by the creator.

     Args:
         sale_log_id(int): ID of the sale that was accepted.

     """
    try:
        sale_log = models.RewardSaleLog.objects.get(id=sale_log_id)
    except models.RewardSaleLog.DoesNotExist:
        return False

    user = sale_log.user
    # Send notification to Socket io with data
    serialized = serializers.RewardSaleLogSerializer(sale_log).data
    data = json.loads(JSONRenderer().render(serialized).decode("utf8"))
    socket_io_service.post_notification_user(data, str(user.pk), "creator-sale-declined")
