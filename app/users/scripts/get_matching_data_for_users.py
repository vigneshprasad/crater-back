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
        tag = user.profile.new_tag.first()
        sign_up_date = user.date_joined.date()
        meetings_count = len(meeting_models.Meeting.objects.filter(participants=user))
        groups_count = len(conversation_models.Group.objects.filter(speakers=user))
        latest_meeting = meeting_models.Meeting.objects.filter(participants=user).last()
        status = latest_meeting.status if latest_meeting else "No previous meeting"
        latest_meeting_preference = meeting_services.get_latest_meeting_preference(user)
        topic = None
        interest = None
        time = None

        if not latest_meeting_preference:
            print(email, " No meeting preference")
        else:
            topic = latest_meeting_preference.topic
            interest = latest_meeting_preference.interests.all()
            time = latest_meeting_preference.time_slots.all()

        print("{} # {} # {} # {} # {} # {} # {} # {} # {} # {}".format(
            email,
            score,
            tag,
            sign_up_date,
            meetings_count,
            groups_count,
            status,
            topic,
            interest,
            time
        ))
