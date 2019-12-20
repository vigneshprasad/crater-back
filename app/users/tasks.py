from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task
from django.core.mail import EmailMessage

from utils.one_signal_service import os_service
from utils.twilio_service import twilio_service


@shared_task(name="send_twilio_message")
def send_twilio_message(phone_number, message):
    return twilio_service.send_message(phone_number, message)


@shared_task(bind=True)
def send_unique_push(self, player_id, contents, data):
    logging.info(f'Send push {player_id}, {contents}, {data}')
    os_service.send_push([player_id], contents, data)


@shared_task(bind=True)
def send_email(self,
               subject: str,
               to: list,
               template_name: str,
               content: dict,
               merge_vars: dict,
               from_email='no-reply@fwmail.scenario-projects.com'):
    msg = EmailMessage(
        subject=subject,
        from_email=from_email,
        to=to
    )
    msg.template_name = template_name
    msg.template_content = content
    msg.merge_vars = merge_vars
    msg.send()
