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

        data = request.data
        sender_pk = data.get("sender")
        message = data.get("message")
        display_name = data.get("display_name")
        group_id = data.get("group")
        message_type = data.get("type")
        message_data = data.get("data")
        firebase_message_id = data.get("id")
        created_at = data.get("created_at")

        # Create group message for the details provided.
        conversation_public.create_group_message(
            sender_pk=sender_pk,
            group_id=group_id,
            message=message,
            display_name=display_name,
            message_type=message_type,
            message_data=message_data,
            firebase_message_id=firebase_message_id,
            created_at=created_at
        )
