from conversations import public as conversation_public
from integrations.freshchat import constants as freshchat_constants, freshchat_service
from integrations.wati import constants
from integrations.wati.services import wati_service_8953, wati_service_9051


def run_with_wati(
        phone_number_list,
        group,
        creator=None,
        account=constants.WATI_9051_ACCOUNT_ENUM,
        dry_run=True
):
    """Send message to phone numbers outside of Crater.

    Args:
        phone_number_list(list): List of phone numbers we are sending
            the message to
        group(Group): Group we are sending the message to.
        creator(Creator): Creator we are sending the message for.
        account(int): Which account of WATI we are sending the message from.
        dry_run(boolean): True for a dry run.

    """
    if not phone_number_list:
        return

    if not creator:
        creator_name = group.host.display_name
    else:
        creator_name = creator.user.display_name

    topic_image_url = group.get_image_url_with_object_url()
    stream_title = group.topic.name

    # Print all the data.
    print("Group ID: {}".format(group.id))
    print("Creator Name: {}".format(creator_name))
    print("Topic Image: {}".format(topic_image_url))
    print("Stream Title: {}".format(stream_title))

    receivers = []
    for phone_number in phone_number_list:
        data = {
            "whatsappNumber": phone_number,
            "customParams": [
                {"name": "stream_image", "value": topic_image_url},
                {"name": "creator_name", "value": creator_name},
                {"name": "stream_starting", "value": constants.STREAM_STARTING_DURATION},
                {"name": "stream_title", "value": stream_title},
                {"name": "session_id", "value": group.id}
            ]
        }
        receivers.append(data)

    if not receivers:
        return

    print("Sending messages to {} numbers".format(len(receivers)))
    print("Receivers data")
    print(receivers)

    if not dry_run:
        response = None
        if account == constants.WATI_9051_ACCOUNT_ENUM:
            print("9051")
            response = wati_service_9051.send_template_messages(
                template_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE,
                receivers=receivers,
                broadcast_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE + "_{}_{}".format(
                    creator_name,
                    group.id
                )
            )
        elif account == constants.WATI_8953_ACCOUNT_ENUM:
            print("8953")
            response = wati_service_8953.send_template_messages(
                template_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE,
                receivers=receivers,
                broadcast_name=constants.STREAM_REMINDER_FOR_FOLLOWER_TEMPLATE + "_{}_{}".format(
                    creator_name,
                    group.id
                )
            )
        print(response)
        print("Sent reminder message")

    print("******")


def run_with_freshchat(phone_number_name_list, group, creator=None, dry_run=True):
    """Send message to phone numbers outside of Crater.

    Args:
        phone_number_name_list(list(tuples)): List of tuples of phone numbers
            and names, we are sending the message to
        group(Group): Group we are sending the message to.
        creator(Creator): Creator we are sending the message for.
        dry_run(boolean): True for a dry run.

    """
    for name, phone_number in phone_number_name_list:
        if not creator:
            creator_name = group.host.display_name
        else:
            creator_name = creator.user.display_name

        print("Creator Name: {}".format(creator_name))

        attendee_name = name
        if not attendee_name:
            attendee_name = freshchat_constants.PLACEHOLDER_NAME_FOR_WHATSAPP
        print("Attendee Name: {}".format(attendee_name))
        topic_name = group.topic.name
        stream_link = conversation_public.get_livestream_link_for_webinar(group)

        data_2 = freshchat_constants.DATA_2_FOR_ATTENDEE_REMINDER.format(
            creator_name=creator_name,
            topic_name=topic_name,
            start_time=group.get_display_start_time()
        )
        data_3 = freshchat_constants.DATA_3_FOR_ATTENDEE_REMINDER.format(
            minutes_remaining=freshchat_constants.WEBINAR_ATTENDEE_REMINDER_DELAY_STR,
            stream_link=stream_link
        )
        print(data_2)
        print(data_3)
        print("Sending reminder message to phone number")
        if not dry_run:
            freshchat_service.freshchat_whatsapp_service.send_outbound_message_to_phone_number(
                phone_number=phone_number,
                template_name=freshchat_constants.WEBINAR_ATTENDEE_REMINDER_TEMPLATE,
                template_data=[
                    {"data": attendee_name},
                    {"data": data_2},
                    {"data": data_3}
                ]
            )
            print("Send reminder to phone number")

        print("******")
