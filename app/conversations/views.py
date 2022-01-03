import datetime

from django.db.models import Q

from rest_framework import mixins
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from users import permissions
from conversations import models
from conversations import serializers
from conversations import services
from conversations import exceptions
from conversations import signals
from conversations import constants
from conversations import paginators
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
        parent_id = self.request.query_params.get("parent", None)
        queryset = self.queryset.filter(type=constants.GROUP_TYPE_GENERIC_ENUM)
        if not parent_id:
            return queryset.filter(parent__isnull=True)
        return queryset.filter(parent__id__contains=parent_id)

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["get"],
        detail=False
    )
    def my(self, request, *args, **kwargs):
        return super(TopicViewSet, self).list(request)

    @action(
        methods=["get"],
        detail=False
    )
    def for_groups(self, request, *args, **kwargs):
        # TODO(Abhishek): Need to add end point to filter only my groups and return count
        user = request.user
        user_groups = services.get_groups_for_user(user)
        response = []
        topic_ids = []

        for group in user_groups:
            topic = group.topic
            # Adding a fail safe.
            if not group.topic:
                continue
            topic_ids.append(topic.parent.id) if topic.parent else topic_ids.append(topic.id)

        all_topics = models.Topic.objects.filter(id__in=topic_ids)
        for topic in all_topics:
            response.append({"topic": serializers.TopicSerializer(topic).data})
        return Response(response)

    @action(
        methods=["get"],
        detail=False
    )
    def ama(self, request, *args, **kwargs):
        queryset = models.Topic.objects.filter(type=constants.GROUP_TYPE_AMA_ENUM, parent=None)
        response = self.get_serializer(queryset, many=True).data
        return Response(response)

    @action(
        methods=["get"],
        detail=False
    )
    def articles(self, request, *args, **kwargs):
        """Returns topics based on articles."""
        queryset = models.Topic.objects.exclude(article__isnull=True).order_by("-created_at")
        serialized = self.get_serializer(queryset, many=True)
        return Response(serialized.data)

    @action(
        methods=["post"],
        detail=False,
        serializer_class=serializers.SuggestedTopicSerializer
    )
    def suggest(self, request, *args, **kwargs):
        """Allows a user to suggest a topic.

        Returns:
            Topic object with the provided name.

        Note:
            If the topic is already present, return 200
            else return 201 created response.

            If the topic is already present the resulting meeting
            will be pre approved.

        """
        request_data = request.data

        # If topic isn"t provided. Raise a bad request.
        suggested_topic = request_data.get("topic")
        if not suggested_topic:
            return self.generate_bad_request(
                {"error": "No Topic provided."}
            )

        suggested_by = request.user

        # Serializer data. Creating suggested topic for the topic.
        # Note: Change the topic to title format.
        data = {
            "topic": suggested_topic.title(),
            "suggested_by": suggested_by.pk,
            "is_approved": True,
            "type": request_data["type"]
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Getting or creating topic with the suggested topic.
        created = False
        try:
            topic = models.Topic.objects.get(name__icontains=instance.name)
        except models.Topic.DoesNotExist:
            topic = models.Topic.objects.create(
                name=instance.name,
                is_active=False,
                is_approved=False,
                is_suggested=True,
                creator=suggested_by,
                type=instance.type,
            )
            created = True

        # Creating topic serialized data for response.
        topic_serialized_data = serializers.TopicSerializer(instance=topic).data

        if not created:
            return Response(
                topic_serialized_data,
                status=status.HTTP_200_OK
            )

        # Only if the topic is created send 201 created response.
        return Response(
            topic_serialized_data,
            status=status.HTTP_201_CREATED
        )


class GroupsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.GroupSerializer
    queryset = models.Group.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Create queryset based on the params."""

        queryset = models.Group.objects.all()
        # Get the user's score.
        topic_ids = self.request.data.get("topics", None)
        if not topic_ids:
            return queryset

        return queryset.filter(
            Q(topic_id__in=topic_ids) | Q(topic__parent_id__in=topic_ids)
        )

    def list(self, request, *args, **kwargs):

        user = request.user
        user_groups = services.get_groups_for_user(user)
        serialized = self.get_serializer(user_groups, many=True)
        return Response(serialized.data)

    @action(
        methods=["get"],
        detail=False
    )
    def my(self, request, *args, **kwargs):
        user = request.user
        groups = self.get_queryset().filter(Q(speakers=user) | Q(host=user)).order_by("start")
        serialized = self.get_serializer(groups, many=True)
        return Response(serialized.data)

    @action(
        methods=["get"],
        detail=False,
    )
    def instant_time_slots(self, request, *args, **kwargs):
        """Returns eligible time slots for instant conversations.

        Note:
            Doesn't send times at which the user already has
            a conversation. Done to prevent creation of
            multiple conversations at the same time.

        """
        user = request.user
        now = datetime.datetime.now()
        eligible_slots = []

        for time in constants.INSTANT_CONVERSATION_TIME_SLOTS:
            slot = datetime.datetime.combine(now.date(), time)
            # If the slot is greater than now time and the user has no
            # conversation at the same time append it to response.
            if slot > now and not services.get_groups_for_user_and_start(user, slot):
                eligible_slots.append(slot)

        if eligible_slots:
            return Response(eligible_slots)

        # If there are no eligible slot of the day, return slots for
        # the next day.
        now = now + datetime.timedelta(days=1)
        for time in constants.INSTANT_CONVERSATION_TIME_SLOTS:
            slot = datetime.datetime.combine(now.date(), time)
            # If user has no conversation at the same time append it to response.
            if not services.get_groups_for_user_and_start(user, slot):
                eligible_slots.append(slot)

        return Response(eligible_slots)

    @action(methods=["post"], detail=False)
    def instant(self, request, *args, **kwargs):
        """Creates a conversation(group) for a user and topic
            selected from client.

        Note:
            Doesn't create conversation if the user already has
            a conversation at the same time.

        """
        user = request.user
        data = request.data
        # Adding request user as host and speaker both.
        data["host"] = user.pk
        data["speakers"] = [user.pk]

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()

            # Sending conversation created signal.
        except exceptions.GroupCreatedAtTheSameTime as e:
            return Response(e.get_error_body(), status=e.status_code)

        # Send signal for conversation created.
        signals.conversation_created.send(
            sender=instance.__class__,
            group=instance
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data)
        )


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

    @action(
        methods=["GET"],
        detail=False,
    )
    def by_date(self, request, *args, **kwargs):
        """Returns optins by date selected by user."""
        user = request.user
        current_preferences = meeting_services.get_current_week_preferences(user, self.get_queryset())
        future_preferences = meeting_services.get_future_week_preferences(user, self.get_queryset())

        all_preferences = list(current_preferences) + list(future_preferences)
        dates_dict = {}

        for preference in all_preferences:
            # Some meeting preferences don't have time slots.
            # Fix for that.
            if not preference.time_slots.first():
                continue

            date = preference.time_slots.first().start.date()
            date_str = str(date)

            if not dates_dict.get(date_str):
                dates_dict[date_str] = [preference]
            else:
                dates_dict[date_str].append(preference)

        response = []
        for date, optins in dates_dict.items():
            response.append(
                {
                    "date": date,
                    "optins": self.get_serializer(optins, many=True).data
                }
            )
        response.sort(key=lambda i: i["date"])

        return Response(response)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(serializer.data)
        # Send a signal on new preference creation.
        signals.new_conversation_registration.send(
            sender=instance.__class__,
            preference=instance
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class RequestViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.RequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.Request.objects.all()

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        group_id = data.get("group")
        participant_type = data.get(
            "participant_type",
            constants.REQUEST_PARTICIPANT_SPEAKER_ENUM
        )

        is_host = services.check_if_user_if_host(
            user,
            group_id
        )

        # If the user rsvping is a host, throw and error.
        if is_host:
            host_rsvp_error = exceptions.HostRSVPError()
            return Response(
                host_rsvp_error.get_error_body(),
                status=host_rsvp_error.status_code
            )

        # Get request for given params.
        request = services.get_request_for_user_and_group_id(
            user,
            group_id,
            participant_type=participant_type
        )

        if request:
            group_already_joined_exceptions = exceptions.GroupAlreadyJoined()
            return Response(
                group_already_joined_exceptions.get_error_body(),
                status=group_already_joined_exceptions.status_code
            )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        group_request = serializer.save()
        headers = self.get_success_headers(serializer.data)

        try:
            if participant_type == constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM:
                result = services.add_attendee_to_group_for_request(
                    user,
                    group_request
                )
            elif participant_type == constants.REQUEST_PARTICIPANT_SPEAKER_ENUM:
                result = services.add_speaker_to_group_for_request(
                    user,
                    group_request
                )
            else:
                invalid_participant_type_exception = exceptions.InvalidParticipantType()
                return Response(
                    invalid_participant_type_exception.get_error_body(),
                    status=invalid_participant_type_exception.status_code
                )

            serializer = self.get_serializer(result)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except (exceptions.GroupMaxSpeakersException, exceptions.GroupJoinedAtTheSameTime) as e:
            return Response(e.get_error_body(), status=e.status_code)

    def retrieve(self, request, *args, **kwargs):

        pk = kwargs.get("pk")
        user = request.user

        # There multiple objects in the backend for now.
        # TODO(Nishant): Cleanup GroupRequest and make 1 request for each user/group.
        group_request = self.get_queryset().filter(
            requester=user,
            group_id=pk,
        ).last()

        if not group_request:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serialized = self.get_serializer(group_request)
        return Response(status=status.HTTP_200_OK, data=serialized.data)


class GroupCalendarViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.GroupSerializer
    queryset = models.Group.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def _make_date_dict(self, queryset):
        dates_list = list(set(queryset.values_list("start__date", flat=True)))
        dates_list.sort()
        data = []
        for date in dates_list:
            items = queryset.filter(
                start__year=date.year,
                start__month=date.month,
                start__day=date.day,
            ).order_by("start")

            data.append({
                "date": str(date),
                "conversations": self.get_serializer(items, many=True).data
            })
        return data

    def get_queryset(self):
        start = self.request.query_params.get("start", None)
        end = self.request.query_params.get("end", None)

        start_datetime = datetime.datetime.strptime(start, constants.DEFAULT_APP_DATETIME_FORMAT) \
            if start else datetime.datetime.now()
        end_datetime = datetime.datetime.strptime(end, constants.DEFAULT_APP_DATETIME_FORMAT) \
            if end else start_datetime + datetime.timedelta(days=7)
        return self.queryset.filter(
            start__date__gte=start_datetime.date(),
            end__date__lte=end_datetime.date(),
        ).order_by("start")

    def list(self, request, *args, **kwargs):
        user = request.user
        user_groups = services.filter_groups_by_score(user, queryset=self.get_queryset())
        response = self._make_date_dict(user_groups)
        return Response(response)

    @action(
        methods=["GET"],
        detail=False
    )
    def my(self, request, *args, **kwargs):
        user = request.user
        groups = self.get_queryset().filter(Q(speakers=user) | Q(host=user) | Q(attendees=user)).order_by("start")
        response = self._make_date_dict(groups)
        return Response(response)


class AllGroupWebinarViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = models.Group.objects.filter(type=constants.GROUP_TYPE_WEBINAR_ENUM)
    serializer_class = serializers.GroupWebinarSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["host", "categories"]


class GroupWebinarViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = models.Group.objects.filter(type=constants.GROUP_TYPE_WEBINAR_ENUM, is_published=True)
    serializer_class = serializers.GroupWebinarSerializer
    pagination_class = paginators.WebinarPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["host", "categories"]

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[permissions.IsAuthenticated]
    )
    def my(self, request):

        user = request.user
        groups = self.filter_queryset(
            self.get_queryset().filter(
                Q(speakers=user) | Q(host=user) | Q(attendees=user)
            ).order_by("start")
        )
        page = self.paginate_queryset(groups)

        if page is None:
            serializer = self.get_serializer(groups, many=True)
            return Response(serializer.data)

        serialized = self.get_serializer(page, many=True)
        return self.get_paginated_response(serialized.data)


class CategoryViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.CategorySerializer
    queryset = models.Category.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class GroupRecodingViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.GroupRecordingSerializer
    queryset = models.GroupRecording.objects.filter(is_published=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ChatReactionViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.ChatReactionSerializer
    queryset = models.ChatReaction.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
