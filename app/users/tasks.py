from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

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
def start_transcoding_for_profile(self, profile_pk):
    from .models import Profile
    logging.info(f'Start transcoding {profile_pk}')
    try:
        profile = Profile.objects.get(pk=profile_pk)
        job_id, uuid = transcoder_service.create_transcoder_job(profile_pk=profile_pk)
        print(job_id, uuid)
        if job_id and uuid:
            profile.transcoder_job_id = job_id
            profile.transcoder_uuid = uuid
            profile._old_cover = profile.cover.url
            profile.transcoder_job_success = False
            profile.cover_thumbnail = ''
            profile.cover_transcoder = ''
            profile.save()
    except Profile.DoesNotExist:
        print(f'Profile does not exist')
        pass


@shared_task(bind=True, name='check_transcoding_for_profile')
def check_transcoding_for_profile(self):
    from .models import Profile
    profiles = Profile.objects.filter(transcoder_job_id__isnull=False, transcoder_job_success=False)
    prefix = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/elastic-transcoder/output/'
    for profile in profiles:
        result = transcoder_service.job_success(profile.transcoder_job_id)
        if result:
            profile.transcoder_job_success = True
            mp4 = f'{prefix}mp4/{profile.transcoder_uuid}.mp4'
            png = f'{prefix}thumbnail/{profile.transcoder_uuid}-00001.png'
            profile.cover_transcoder = mp4
            profile.cover_thumbnail = png
            profile.transcoder_job_id = None
            profile.save()
