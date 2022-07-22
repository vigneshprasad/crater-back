import datetime
import json

from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from users import permissions

from conversations import serializers as conversation_serializers

from integrations.firebase.service import firebase_service
from conversations import public as conversation_public


class FirebaseViewSet(GenericViewSet):

    permission_classes = [permissions.IsAuthenticated]

    @action(
        methods=["GET"],
        detail=False
    )
    def token(self, request):
        """Register a user on firebase and return access token."""
        user = request.user
        token = firebase_service.register(user)
        user_data = conversation_serializers.GroupChatUserSerializer(user).data
        firebase_service.set_document(
            str(user.pk),
            "user_details",
            user_data
        )

        return Response({"token": token})


class FirebaseMessageViewSet(GenericViewSet):

    permission_classes = [permissions.AllowAny]

    @action(
        methods=["POST"],
        detail=False
    )
    def collect(self, request):
        """Collects messages sent to firebase and populates
            them in our database.

        """
        data = dict(request.data)
        try:
            sender_pk = data["sender"]
            message = data["message"]
            display_name = data.get("displayName")
            group_id = int(data["group"])
            message_type = data["type"]
            message_data = data.get("data")
            firebase_message_id = data["id"]
            created_at = data["createdAt"]
            # Convert created at to python datetime.
            created_at_datetime = datetime.datetime.strptime(
                created_at,
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        # Create group message for the details provided.
        conversation_public.create_group_message(
            sender_pk=sender_pk,
            group_id=group_id,
            message=message,
            display_name=display_name,
            message_type=message_type,
            message_data=message_data,
            firebase_message_id=firebase_message_id,
            created_at=created_at_datetime
        )

        return Response(status=status.HTTP_201_CREATED)
