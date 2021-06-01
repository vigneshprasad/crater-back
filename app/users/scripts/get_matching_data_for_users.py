import pytz
from django.conf import settings

from resources.meetings import models as meeting_models
from resources.meetings import services as meeting_services
from conversations import models as conversation_models
from users import models


def get_matching_data_for_users(emails):

    print("Number of emails: {}".format(len(emails)))
    users = models.User.objects.filter(email__in=emails)
    print("Number of users: {}".format(users.count()))

    for user in users:
        email = user.email
        score = user.score
        if not user.profile:
            print(email, "No Profile")
            continue

        tag = user.profile.new_tag.first()
        sign_up_date = user.date_joined.date()
        meetings_count = len(meeting_models.Meeting.objects.filter(participants=user))
        groups_count = len(conversation_models.Group.objects.filter(speakers=user))
        latest_meeting = meeting_models.Meeting.objects.filter(participants=user).last()
        status = latest_meeting.status if latest_meeting else "No previous meeting"
        latest_meeting_preference = meeting_services.get_latest_meeting_preference(user)
        topic_name = None
        interests_list = None
        times_list = None

        local_tz = pytz.timezone(settings.TIME_ZONE)

        if not latest_meeting_preference:
            print(email, " No meeting preference")
        else:
            topic_name = latest_meeting_preference.topic.name if latest_meeting_preference.topic else None
            interests_list = [interest.name for interest in latest_meeting_preference.interests.all()]
            times_list = [time_slot.start.astimezone(tz=local_tz).strftime("%d/%m/%y %H:%M") for time_slot in latest_meeting_preference.time_slots.all()]

        print("{} # {} # {} # {} # {} # {} # {} # {} # {} # {}".format(
            email,
            score,
            tag.name if tag else None,
            sign_up_date,
            meetings_count,
            groups_count,
            status,
            topic_name,
            interests_list,
            times_list
        ))
