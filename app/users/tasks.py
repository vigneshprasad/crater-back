from __future__ import absolute_import, unicode_literals
from celery import shared_task
from utils.twilio_service import twilio_service
from utils.one_signal_service import os_service
import logging


@shared_task(name="send_twilio_message")
def send_twilio_message(phone_number, message):
    return twilio_service.send_message(phone_number, message)


@shared_task(bind=True)
def send_unique_push(self, player_id, contents, data):
    logging.info(f'Send push {player_id}, {contents}, {data}')
    os_service.send_push([player_id], contents, data)
