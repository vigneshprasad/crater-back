import os

import requests


class SocketIOService:
    API_BASE_URL = os.environ.get('SOCKET_IO_BASE_URL')

    API_URL = {
        "user_permission": "/user-permission/"
    }

    def get_api_endpoint(self, name: str):
        return "%s%s" % (self.API_BASE_URL, self.API_URL.get(name))

    def send_user_permission(self, data):
        payload = {
            "user_id": str(data.user.pk),
            "id": data.id,
            "allow_create_stream": data.allow_create_stream,
            "allow_chat": data.allow_chat
        }

        response = requests.post(
            self.get_api_endpoint("user_permission"),
            json=payload,
        ).json()
        return response



socket_io_service = SocketIOService()