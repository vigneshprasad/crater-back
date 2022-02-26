from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from users import permissions

from conversations import serializers as conversation_serializers

from integrations.firebase.service import firebase_service


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
