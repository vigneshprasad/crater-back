from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from users import permissions
from group_meetings import models
from group_meetings import private
from group_meetings import serializers


class CategoryViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.CategorySerializer
    queryset = models.Category.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]


class AgendaViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.AgendaSerializer
    queryset = models.Agenda.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]


class GroupsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.GroupSerializer
    queryset = models.Group.objects.filter(closed=False)
    permission_classes = [permissions.IsAuthenticated]


class InviteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.AgendaSerializer
    queryset = models.Invite.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["post"],
        detail=False
    )
    def accepted(self, request, *args, **kwargs):
        request_data = request.data
        invite_id = request_data.get("invite")

        try:
            invite = models.Invite.objects.get(id=invite_id)
        except models.Invite.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Invite is invalid."}
            )

        if invite.invitee_id != request.user.pk:
            return self.generate_bad_request(
                {"error": "You can't accept this invite."}
            )

        invite.mark_status_as_accepted()
        private.update_group_on_invite_acceptance(invite)

        return Response({"status": "success"})

    @action(
        methods=["post"],
        detail=False
    )
    def declined(self, request, *args, **kwargs):
        request_data = request.data
        invite_id = request_data.get("invite")

        try:
            invite = models.Invite.objects.get(id=invite_id)
        except models.Invite.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Invite is invalid."}
            )

        # Check if the invitee is accepting the invite and no one else.
        if invite.invitee_id != request.user.pk:
            return self.generate_bad_request(
                {"error": "You can't decline this invite."}
            )

        invite.mark_status_as_declined()
        return Response({"status": "success"})


class RequestViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.AgendaSerializer
    queryset = models.Request.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["group"]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["post"],
        detail=False
    )
    def accepted(self, request, *args, **kwargs):
        request_data = request.data
        request_id = request_data.get("request")
        approved_by = request.user

        try:
            request = models.Request.objects.get(id=request_id)
        except models.Request.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Request is invalid."}
            )

        if not private.can_respond_to_requests(approved_by, request):
            return self.generate_bad_request(
                {"error": "You can't respond to requests."}
            )

        request.mark_status_as_accepted()
        private.update_group_on_request_acceptance(request)

        return Response({"status": "success"})

    @action(
        methods=["post"],
        detail=False
    )
    def declined(self, request, *args, **kwargs):
        request_data = request.data
        request_id = request_data.get("request")
        approved_by = request.user

        try:
            request = models.Request.objects.get(id=request_id)
        except models.Request.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Request is invalid."}
            )

        if not private.can_respond_to_requests(approved_by, request):
            return self.generate_bad_request(
                {"error": "You can't respond to requests."}
            )

        request.mark_status_as_declined()
        return Response({"status": "success"})
