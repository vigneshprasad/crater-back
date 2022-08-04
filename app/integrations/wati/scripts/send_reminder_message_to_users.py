from integrations.wati import constants
from integrations.wati.services import wati_service_9051


def run(phone_number_list, group, creator=None, dry_run=False):
    """Send message to phone numbers outside of Crater.

    Args:
        phone_number_list(list): List of phone numbers we are sending
            the message to
        group(Group): Group we are sending the message to.
        creator(Creator): Creator we are sending the message for.
        dry_run(boolean): True for a dry run.

    """
    if not phone_number_list:
        return

    if not creator:
        creator_name = group.host.display_name
    else:
        creator_name = creator.user.display_name

    topic_image_url = group.topic.image.url
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
        wati_service_9051.send_template_messages(
            template_name=constants.STREAM_REMINDER_FOR_ATTENDEE_TEMPLATE_9501,
            receivers=receivers,
            broadcast_name="Outside Phonenumbers" + "_{}".format(group.id)
        )
        print("Sent reminder message")
