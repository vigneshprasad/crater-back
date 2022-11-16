import requests
import logging

from django.conf import settings

LOGGER = logging.getLogger(__name__)


class SocketIOService:
    """API service for socket."""

    API_BASE_URL = settings.SOCKET_IO_BASE_URL
    API_URL = {
        "user_permission": "/user-permission/",
        "notification_user": "/notification/user/",
        "viewer_count_change": "/group-helper/update/"
    }

    def get_api_endpoint(self, name: str):
        """Return API endpoint for a view name.

        Args:
            name(str): Name of the view.

        """
        return "%s%s" % (self.API_BASE_URL, self.API_URL.get(name))

    def send_user_permission(self, data):
        """Sends user permission data to socket.io for updating
            user chat permissions.

        """
        payload = {
            "user_id": str(data.user.pk),
            "id": data.id,
            "allow_create_stream": data.allow_create_stream,
            "allow_chat": data.allow_chat,
            "show_viewer_count": data.show_viewer_count,
        }

        # Raise exception if the request fails for some reason.
        try:
            response = requests.post(
                self.get_api_endpoint("user_permission"),
                json=payload,
            ).json()
        except Exception as e:
            LOGGER.error(str(e))
            return

        return response

    def post_notification_user(self, data, user_id, type_key):
        """Sends notification data for a user to socket.io server.

        Args:
            data(json): Serialised data for the message.
            user_id(str): PK of user wer are sending the
                notification to.
            type_key(str): Type of notification we are sending.

        """

        payload = {
            "user": user_id,
            "type": type_key,
            "data": data
        }

        try:
            response = requests.post(
                self.get_api_endpoint("notification_user"),
                json=payload
            ).json()
        except Exception as e:
            LOGGER.error(str(e))
            return

        return response

    def post_viewer_count_update(self, group_id):
        """Post viewer count to socket.

        Args:
            group_id(int): ID of group where viewer count
                has changed.

        """
        payload = {"group_id": group_id}

        try:
            response = requests.post(
                self.get_api_endpoint("viewer_count_change"),
                json=payload
            ).json()
        except Exception as e:
            LOGGER.error(str(e))
            return

        return response


socket_io_service = SocketIOService()
