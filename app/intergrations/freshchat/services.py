# {
#       "from": {
#         "phone_number": "+919999999999"
#       },
#       "provider": "whatsapp",
#       "to": {
#         "phone_number": "+919999999999"
#       },
#       "data": {
#         "message_template": {
#           "template_name": "hello_world",
#           "namespace": "XXXXXXXX_XXXX_XXXX_XXXX_XXXXXXXXXXXX",
#           "language": {
#             "policy": "deterministic",
#             "code": "en_US"
#           },
#           "rich_template_data": {
#             "header": {
#               "type": "video",
#               "media_url": "https://sample.in/sample.mkv"
#             },
#            "body": {
#               "params": [
#                 {"data": "John Doe"}
#              ]
#             }
#           }
#         }
#       }
# }

import requests

from intergrations.freshchat import constants
from intergrations.freshchat import utils


def send_meeting_reminder_outbound_message_to_user(user, time):
    template_name = constants.MEETING_REMINDER_FRESHCHAT_TEMPLATE
    message_data = {
        "template_name": template_name,
        "namespace": constants.FRESHCHAT_OUTBOUND_TEMPLATE_NAMESPACE,
        "body": {
            "params": [
                {"data": time}
            ]
        }
    }
    template_data = {
        "from": {
            "phone_number": constants.FRESHCHAT_MESSAGING_PHONE_NUMBER
        },
        "to": {
            "phone_number": user.get_phone_number()
        },
        "provider": constants.FRESHCHAT_DEFAULT_PROVIDER,
        "data": message_data
    }

    response = requests.post(
        url=constants.FRESHCHAT_BASE_URL + "/outbound-messages/whatsapp",
        headers=utils.get_request_header(),
        data=template_data
    )

    print(response.__dict__)
