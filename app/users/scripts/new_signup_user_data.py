import datetime

from users import models
from resources.meetings import models as meeting_models
from resources.meetings import services as meeting_services
from conversations import models as conversation_models
from conversations import services as conversation_services


def get_users_between_start_and_end(start_date, end_date):
    start = start_date
    end = start_date + datetime.timedelta(days=7)

    if end > end_date:
        end = end_date

    while end <= end_date:
        print("*"*30)
        print("Data for week {} - {}".format(start, end))
        users = models.User.objects.filter(
            date_joined__gte=start,
            date_joined__lt=end)

        for user in users:
            if not user.has_profile:
                continue
            profile = user.profile

            user_tag = profile.new_tag.first()
            user_tag_name = user_tag.name if user_tag else None

            user_experience = profile.years_of_experience
            user_experience_str = dict(models.Profile.YEARS_OF_EXPERIENCE_CHOICES)[
                profile.years_of_experience] if user_experience else None

            introduction = profile.get_introduction() or ""
            user_introduction = introduction.replace("\n", "")

            # Printing in csv format with # as the separator.
            print(
                user.email, "#",
                user.date_joined.date(), "#",
                user.phone_number_verified, "#",
                user_tag_name, "#",
                user_experience_str, "#",
                profile.linkedin_url, "#",
                user.score, "#",
                user.new_source.name if user.new_source else None, "#",
                meeting_services.get_meetings_attended(user).count(), "#",
                conversation_services.get_groups_for_user(user).count(), "#",
                meeting_models.MeetingPreference.objects.filter(user=user).count(), "#",
                user_introduction
            )

        start = end
        end = start + datetime.timedelta(days=7)
