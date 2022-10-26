from __future__ import absolute_import, unicode_literals

import datetime
import logging

from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.utils import timezone

from integrations.dyte import models as dyte_models
from integrations.onesignal.services import one_signal_service
from users import constants, models
from utils.transcoder_service import transcoder_service

LOGGER = logging.getLogger(__name__)


@shared_task(bind=True)
def send_unique_push(self, player_id, contents, data):
    logging.info(f'Send push {player_id}, {contents}, {data}')
    one_signal_service.send_push([player_id], contents, data)


@task
def send_email(
        subject: str,
        to: list,
        template_name: str,
        content: dict,
        merge_vars: dict,
        **kwargs
):
    # Get optional arguments from kwargs.
    reply_to = kwargs.get('reply_to', [])
    cc = kwargs.get('cc', [])
    bcc = kwargs.get('bcc', [])
    from_email = kwargs.get('from_email', settings.DEFAULT_FROM_EMAIL)

    msg = EmailMessage(
        subject=subject,
        from_email=from_email,
        to=to,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to
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
    files = CoverFile.objects.filter(
        profiles__isnull=True,
        masterclasses__isnull=True,
        post_files__isnull=True,
        created__lte=one_day_ago
    )
    files.delete()


@periodic_task(run_every=crontab(minute="0", hour="*/1"))
def update_user_referrals_status():
    """Update user referral status from `User Action Pending`
        to `Due` based on whether the referred user has watched
        a stream for 20 minutes or more.

    Note:
        Checking only for stream happening today, since it's not
            likely for users to watch previous streams.

    """
    # Get all user referrals which is in `User Action Pending` state.
    today = datetime.date.today()
    pending_referrals = models.UserReferral.objects.filter(
        status=constants.REFERRAL_STATUS_USER_ACTION_PENDING_ENUM
    )
    user_ids_with_pending_referrals = pending_referrals.values_list("user_id", flat=True)

    if not user_ids_with_pending_referrals:
        return

    # Get meeting participants for today that went live.
    dyte_meeting_participants = dyte_models.DyteMeetingParticipant.objects.filter(
        participant__in=user_ids_with_pending_referrals,
        last_online_at__isnull=False,
        dyte_meeting__group__start__gte=today,
        dyte_meeting__group__closed=True,
    )

    updated_users = []
    for dyte_meeting_participant in dyte_meeting_participants:
        # Get time spent on stream in minutes by the referred user.
        participant = dyte_meeting_participant.participant
        if participant in updated_users:
            continue

        time_spent_on_stream = float(dyte_meeting_participant.minutes_spent or 0)
        if not time_spent_on_stream >= 20:
            continue

        # Only one referral per user will be present.
        referral = pending_referrals.filter(user=participant).first()
        referral.mark_payment_due(stream=dyte_meeting_participant.dyte_meeting.group)
        updated_users.append(dyte_meeting_participant.participant)


@task
def create_profile_on_user_creation(user_pk):
    """Create profile for new user.

    Args:
        user_pk(uuid): UUID for created user.

    """
    try:
        user = get_user_model().objects.get(pk=user_pk)
        models.Profile.objects.get_or_create(user=user)
    except Exception as e:
        LOGGER.error(str(e))
        return
