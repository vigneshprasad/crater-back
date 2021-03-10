from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action

from users import permissions
from integrations.agora import private


class AgoraChannelAuthentication(GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["get"],
        detail=False,
    )
    def token(self, request):
        """Creates token for agora video/audio call.

        Required:
            channel_id: ID of group object the the user is
                trying to join.

        """
        request_data = request.data
        user = request.user
        channel_id = request_data.get("channel_id")

        # Try to create token else return a 400, and log the error to Sentry.

        try:
            token, channel_name = private.generate_token_for_user_and_group(user, channel_id)
        except Exception as e:
            logging.error("Agora token generation failed: {}".format(str(e)))
            return self.generate_bad_request(
                {"error": "Token creation failed."}
            )

        return Response({"token": token, "channel_name": channel_name})