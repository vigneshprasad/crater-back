import requests
import logging

from django.conf import settings

LOGGER = logging.getLogger(__name__)


class SocketIOService:
    """API service for socket."""

    API_BASE_URL = settings.SOCKET_IO_BASE_URL
    API_URL = {
        "user_permission": "/user-permission/"
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


socket_io_service = SocketIOService()
