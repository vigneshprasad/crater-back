from conversations import models
from conversations import constants


def run():
    """Get all emails for attendees for each category
        for FB ads retargeting.

    """
    categories = models.Category.objects.all()

    for category in categories:
        print("{}".format(category.name), "-"*30)

        # Get all webinars with the category.
        groups = models.Group.objects.filter(
            categories=category,
            type=constants.GROUP_TYPE_WEBINAR_ENUM
        )
        all_attendees = []
        for group in groups:
            group_attendees = group.attendees.all()
            all_attendees += group_attendees

        # Make sure the emails are unique for each category.
        all_attendees = list(set(all_attendees))

        for attendee in all_attendees:
            # If attendee email is not present, don't print the value.
            if not attendee.email:
                continue
            print(attendee.email)

        print("-" * 30)
