import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from integrations.agora import private
from group_meetings import models as group_models


class AgoraChannelAuthentication(APIView):

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def token(self, request):
        request_data = request.data
        user = request.user
        group_id = request_data.get("group_id")

        try:
            group = group_models.Group.objects.get(id=group_id)
        except group_models.Group.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Invalid group id."}
            )

        # Try to create token else return a 400, and log the error to Sentry.
        try:
            token = private.generate_token_for_user_and_group(user, group)
        except Exception as e:
            logging.error("Agora token generation failed: {}".format(str(e)))
            return self.generate_bad_request(
                {"error": "Token creation failed."}
            )

        return Response({"token": token})
