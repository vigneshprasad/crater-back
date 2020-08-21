from intergrations.freshchat import constants


def get_request_header():
    return {
        "Accept": "application/json",
        "Authorization": "Bearer {}".format(
            constants.FRESHCHAT_ACCESS_TOKEN
        ),
        "Content-Type": "application/json"
    }
