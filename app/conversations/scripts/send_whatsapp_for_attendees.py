from conversations import models
from integrations.freshchat import constants as freshchat_constants
from integrations.freshchat import freshchat_service


def run(group_id, link, users=None, dry_run=True):

    group = models.Group.objects.get(id=group_id)
    all_users = users if users else group.attendees.all()

    for user in all_users:
        print("-------")
        attendee_name = user.get_display_first_name()
        creator_name = group.host.display_name

        if not attendee_name:
            # Not throwing error since we can't fix
            # this without user input.
            continue

        topic_name = group.topic.name
        stream_link = link

        data_2 = freshchat_constants.DATA_2_FOR_ATTENDEE_REMINDER.format(
            creator_name=creator_name,
            topic_name=topic_name,
            start_time=group.get_display_start_time()
        )
        data_3 = freshchat_constants.DATA_3_FOR_ATTENDEE_REMINDER.format(
            minutes_remaining="10 minutes",
            stream_link=stream_link
        )

        template_data = [
            {"data": attendee_name},
            {"data": data_2},
            {"data": data_3}
        ]
        print(user)
        if dry_run:
            print(template_data)

        if not dry_run:
            profile = user.profile
            # Mark opted for whatsapp true.
            profile.opted_in_for_whatsapp = True
            profile.save()
            user.refresh_from_db()
            status = freshchat_service.freshchat_whatsapp_service.send_outbound_message(
                user=user,
                template_name=freshchat_constants.WEBINAR_ATTENDEE_REMINDER_TEMPLATE,
                template_data=[
                    {"data": attendee_name},
                    {"data": data_2},
                    {"data": data_3}
                ]
            )
            print(status)
            # Marking it false again.
            profile.opted_in_for_whatsapp = False
            profile.save()

        print("-------")
