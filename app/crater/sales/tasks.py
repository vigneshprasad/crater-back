import json
from operator import mod
from celery.task import task

from crater.sales import models
from crater.sales import serializers
from utils.socket_io_service import socket_io_service

from rest_framework.renderers import JSONRenderer


@task()
def send_notification_to_creator_for_sale(sale_log_id):
    """Send web/mobile notification to creator is a user
        purchases a reward.

    """
    try:
        sale_log = models.RewardSaleLog.objects.get(id=sale_log_id)

    except models.RewardSaleLog.DoesNotExist:
        return

    creator = sale_log.reward_sale.reward.creator.user
    user = sale_log.user

    # Send notification to Socket io with data
    serialized = serializers.RewardSaleLogSerializer(sale_log).data
    data = json.loads(JSONRenderer().render(serialized).decode("utf8"))
    socket_io_service.post_notification_user(data, str(creator.pk), "creator-sale-request")


@task()
def send_notification_user_sale_accepted(sale_log_id):
    try:
        sale_log = models.RewardSaleLog.objects.get(id=sale_log_id)

    except models.RewardSaleLog.DoesNotExist:
        return

    creator = sale_log.reward_sale.reward.creator.user
    user = sale_log.user

    # Send notification to Socket io with data
    serialized = serializers.RewardSaleLogSerializer(sale_log).data
    data = json.loads(JSONRenderer().render(serialized).decode("utf8"))
    socket_io_service.post_notification_user(data, str(user.pk), "creator-sale-accepted")


@task()
def send_notification_user_sale_declined(sale_log_id):
    try:
        sale_log = models.RewardSaleLog.objects.get(id=sale_log_id)

    except models.RewardSaleLog.DoesNotExist:
        return

    creator = sale_log.reward_sale.reward.creator.user
    user = sale_log.user

    # Send notification to Socket io with data
    serialized = serializers.RewardSaleLogSerializer(sale_log).data
    data = json.loads(JSONRenderer().render(serialized).decode("utf8"))
    socket_io_service.post_notification_user(data, str(user.pk), "creator-sale-declined")