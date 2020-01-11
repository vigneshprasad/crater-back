from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from utils.one_signal_service import os_service
from utils.transcoder_service import transcoder_service
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


@shared_task(bind=True)
def start_transcoding_for_cover_file(self, cover_file_pk):
    from .models import CoverFile
    logging.info(f'Start transcoding file {cover_file_pk}')
    try:
        cover_file = CoverFile.objects.get(pk=cover_file_pk)
        job_id, uuid = transcoder_service.create_file_transcoder_job(cover_file_pk=cover_file_pk)
        print(job_id, uuid)
        if job_id and uuid:
            cover_file.transcoder_job_id = job_id
            cover_file.transcoder_uuid = uuid
            cover_file.save()
    except CoverFile.DoesNotExist:
        print(f'Profile does not exist')
        pass


@shared_task(bind=True, name='check_transcoding_for_cover_file')
def check_transcoding_for_cover_file(self):
    from .models import CoverFile
    files = CoverFile.objects.filter(transcoder_job_id__isnull=False, transcoder_job_success=False)
    prefix = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/elastic-transcoder/output/'
    for file in files:
        result = transcoder_service.job_success(file.transcoder_job_id)
        if result:
            file.transcoder_job_success = True
            mp4 = f'{prefix}mp4/{file.transcoder_uuid}.mp4'
            png = f'{prefix}thumbnail/{file.transcoder_uuid}-00001.png'
            file.cover_transcoder = mp4
            file.cover_thumbnail = png
            file.save()


@shared_task(bind=True, name='auto_remove_not_used_cover_files')
def auto_remove_not_used_cover_files(self):
    from .models import CoverFile
    one_day_ago = timezone.now() - timezone.timedelta(days=1)
    files = CoverFile.objects.filter(profiles__isnull=True, created__lte=one_day_ago)
    files.delete()
