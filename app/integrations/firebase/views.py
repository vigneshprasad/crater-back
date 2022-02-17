from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from users import permissions

from conversations import serializers as conversation_serializers

from integrations.firebase.service import firebase


class FirebaseViewSet(GenericViewSet):
  permission_classes = [permissions.IsAuthenticated]
  
  @action(
    methods=["GET"],
    detail=False
  )
  def token(self, request):
    user = request.user
    token = firebase.register_user(user)

    user_data = conversation_serializers.GroupChatUserSerializer(user).data
    firebase.set_document(str(user.pk), "user_details", user_data)

    return Response({
      "token": token
    })
