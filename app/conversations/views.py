from django.db.models import Q

from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from users import permissions
from conversations import models, serializers, services

from resources.meetings import services as meeting_services
from resources.meetings import models as meeting_models


class TopicViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.TopicSerializer
    queryset = models.Topic.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        parent_id = self.request.query_params.get('parent', None)
        if parent_id is not None:
            return self.queryset.filter(parent__id__contains=parent_id)
        return self.queryset.filter(parent=None)

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["get"],
        detail=False
    )
    def my(self, request, *args, **kwargs):
        return super(TopicViewSet, self).list(request)


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

    @action(
        methods=["get"],
        detail=False
    )
    def my(self, request, *args, **kwargs):
        user = request.user
        groups = models.Group.objects.filter(Q(speakers=user) | Q(host=user))
        serialized = self.get_serializer(groups, many=True)
        return Response(serialized.data)


class OptinViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.OptinSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = meeting_models.MeetingPreference.objects.all()

    def list(self, request, *args, **kwargs):
        user = request.user
        current_preferences = meeting_services.get_current_week_preferences(user, self.get_queryset())
        future_preferences = meeting_services.get_future_week_preferences(user, self.get_queryset())

        all_preferences = list(current_preferences) + list(future_preferences)
        serialized = self.get_serializer(all_preferences, many=True)
        return Response(serialized.data)


class RequestViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.RequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.Request.objects.all()

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group_request = serializer.save()
        headers = self.get_success_headers(serializer.data)

        # Add user to group and update status to confirmed
        updated_request = services.update_request_and_add_user_to_group(user, group_request)

        serializer = self.get_serializer(updated_request)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
