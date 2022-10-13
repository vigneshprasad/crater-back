import datetime
from random import randint

from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from conversations import constants, filters, models, paginators, serializers
from users import permissions as user_permissions

User = get_user_model()


class GroupWebinarPublicViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.GroupWebinarSerializer
    queryset = models.Group.objects.filter(
        type=constants.GROUP_TYPE_WEBINAR_ENUM,
        is_published=True
    ).select_related(
        "topic", "host__profile", "recording",
    ).order_by(
        "closed", "is_live", "start"
    ).prefetch_related(
        "categories",
        "interests",
        Prefetch("attendees", User.objects.select_related("profile")),
        Prefetch("speakers", User.objects.select_related("profile")),
    )
    permission_classes = [user_permissions.AllowAny]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.AllWebinarsFilters
    filterset_fields = ["categories"]

    def _get_upcoming_webinars(self):
        """Return upcoming webinars."""
        return self.get_queryset().filter(
            is_live=False,
            closed=False,
            privacy=constants.GROUP_PRIVACY_PUBLIC_ENUM,
            start__gte=datetime.datetime.now()
        )

    def _get_live_webinars(self):
        """Return live webinars."""
        return self.get_queryset().filter(
            is_live=True,
            privacy=constants.GROUP_PRIVACY_PUBLIC_ENUM,
            closed=False
        ).exclude(
            categories__name="Hacking"
        )

    def _get_past_webinars_with_recordings(self, featured=False):
        """Return past webinars with published recordings."""

        groups_with_recordings = self.get_queryset().filter(
            start__lte=datetime.datetime.now(),
            recording__isnull=False
        )
        # Get group with recording objects which are published
        # and have recording object present.
        published_groups_with_recording = groups_with_recordings.filter(
            recording__recording__isnull=False,
            recording__is_published=True
        ).order_by("-start")

        if not featured:
            return published_groups_with_recording

        return published_groups_with_recording.filter(recording__featured=True)

    def _get_featured_webinars(self):
        """Return featured webinars.

        Note:
            Only featured webinars in the future will
                show up. If a featured webinar is
                live don't show in this list.

        """
        min_start = datetime.datetime.now() - datetime.timedelta(hours=1)
        return self.get_queryset().filter(
            is_featured=True,
            is_live=False,
            closed=False,
            start__gte=min_start
        )

    @staticmethod
    def _get_past_streams_with_featured_recordings(past_streams):
        """Return past stream with featured recordings.

        Args:
            past_streams(list/queryset): List of past streams from which
                we are getting the featured past streams.

        """
        featured_streams = []
        for category in constants.PAST_STREAM_FEATURED_CATEGORIES:
            past_streams_category = past_streams.filter(categories__name=category)
            if not past_streams_category:
                continue
            random_index = randint(0, len(past_streams_category) - 1)
            featured_streams.append(past_streams_category[random_index])

        return featured_streams

    @action(
        methods=["GET"],
        detail=False,
        pagination_class=paginators.FeaturedWebinarPagination,
        queryset=models.Group.objects.filter(
            type=constants.GROUP_TYPE_WEBINAR_ENUM,
            is_published=True
        ).exclude(
            categories__name="Hacking"
        ).select_related(
            "topic",
            "host__profile",
            "host__creator",
            "recording",
        ).order_by("-start"),
        serializer_class=serializers.StreamListSerializer,
        filterset_fields=["host"]
    )
    def featured(self, request):
        """Return list of webinars that has to featured for Crater club.

        Note:
            Returns list of live and featured webinars.

        """
        live_groups = self.filter_queryset(self._get_live_webinars())
        featured_groups = self.filter_queryset(self._get_featured_webinars())
        featured_streams_next_hour = False

        if not live_groups:
            # Filter featured streams within the next 1 hour
            now = datetime.datetime.now()
            next_hour_datetime = now + datetime.timedelta(hours=1)
            featured_streams_next_hour = featured_groups.filter(start__lte=next_hour_datetime)

        # If there are no live groups and featured stream in the next one hour.
        if featured_streams_next_hour or live_groups:
            featured_streams = self.filter_queryset(
                live_groups | featured_groups
            ).order_by("-is_live", "start")
        else:
            self.serializer_class = serializers.StreamWithRecordingListSerializer
            past_streams_with_recording = self.filter_queryset(
                self._get_past_webinars_with_recordings(featured=True)
            )
            featured_streams = self._get_past_streams_with_featured_recordings(
                past_streams=past_streams_with_recording
            )

        page = self.paginate_queryset(featured_streams)

        if page is None:
            serializer = self.get_serializer(featured_streams, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["GET"],
        detail=False,
        pagination_class=paginators.FeaturedWebinarPagination,
        queryset=models.Group.objects.filter(
            type=constants.GROUP_TYPE_WEBINAR_ENUM,
            is_published=True
        ).exclude(
            categories__name="Hacking"
        ).select_related(
            "topic",
            "host__profile",
            "host__creator"
        ).order_by("-start"),
        serializer_class=serializers.StreamListSerializer,
        filterset_fields=["host", "categories"]
    )
    def upcoming(self, request):
        """Return webinars which are in the future.

        Note:
            Return groups queryset sorted by start of
            the groups.

        """
        queryset = self.filter_queryset(self._get_upcoming_webinars()).order_by("start", "-created_at")
        page = self.paginate_queryset(queryset)

        if page is None:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["GET"],
        detail=False,
        filterset_fields=["host"]
    )
    def live(self, request):
        """Return webinars which are in live right now.

        Note:
            Return groups queryset sorted by start of
            the groups.

        """
        queryset = self.filter_queryset(self._get_live_webinars()).order_by("start")
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        filterset_fields=["host"],
    )
    def all(self, request):
        """Return all webinars live and upcoming."""

        queryset_live = self._get_live_webinars()
        queryset_upcoming = self._get_upcoming_webinars()

        queryset = self.filter_queryset(
            queryset_live | queryset_upcoming
        ).order_by("-is_live", "start")
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        pagination_class=paginators.FeaturedWebinarPagination,
        queryset=models.Group.objects.filter(
            type=constants.GROUP_TYPE_WEBINAR_ENUM,
            is_published=True,
            categories__name="Hacking"
        ).select_related(
            "topic",
            "host__profile",
            "host__creator"
        ).order_by("-start"),
        serializer_class=serializers.StreamListSerializer,
        filterset_fields=["host", "categories"]
    )
    def hacking(self, request):
        """Return webinars which are in hacking category

        Note:
            Return groups queryset sorted by start of
            the groups.

        """
        queryset = self.filter_queryset(self._get_upcoming_webinars()).order_by("start", "-created_at")
        page = self.paginate_queryset(queryset)

        if page is None:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["GET"],
        detail=False,
        pagination_class=paginators.WebinarPagination,
        queryset=models.Group.objects.filter(
            type=constants.GROUP_TYPE_WEBINAR_ENUM,
            is_published=True
        ).exclude(
            categories__name="Hacking"
        ).select_related(
            "topic",
            "host__profile",
            "host__creator"
        ).order_by("-start"),
        serializer_class=serializers.StreamPastListSerializer,
        filterset_fields=["host", "categories"],
    )
    def past(self, request):
        """Returns past webinars."""
        queryset = self.filter_queryset(self._get_past_webinars_with_recordings())
        page = self.paginate_queryset(queryset)

        if page is None:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["GET"],
        detail=False,
        pagination_class=paginators.WebinarPagination,
        queryset=models.Group.objects.filter(
            type=constants.GROUP_TYPE_WEBINAR_ENUM,
            is_published=True
        ).exclude(
            categories__name="Hacking"
        ).select_related(
            "topic",
            "host__profile",
            "host__creator",
            "recording"
        ).order_by("-start"),
        serializer_class=serializers.StreamWithRecordingListSerializer,
        filterset_fields=["host", "categories"],
    )
    def videos(self, request):
        """Returns past webinars with published recordings."""
        queryset = self.filter_queryset(self._get_past_webinars_with_recordings())
        page = self.paginate_queryset(queryset)

        if page is None:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class SeriesPublicViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.SeriesSerializer
    queryset = models.Series.objects.filter(is_published=True).select_related(
        "topic", "host"
    )
    permission_classes = [user_permissions.AllowAny]
    pagination_class = paginators.WebinarPagination

    def get_object(self):
        queryset = self.queryset.select_related(
            "topic__article", "topic__parent", "host__profile"
        ).prefetch_related(
            "categories",
            Prefetch(
                "groups",
                models.Group.objects
                .select_related("topic", "host__profile", "recording", )
                .order_by("closed", "is_live", "start")
                .prefetch_related(
                    "categories",
                    "interests",
                    Prefetch("attendees", User.objects.select_related("profile")),
                    Prefetch("speakers", User.objects.select_related("profile")),
                )
            )
        )
        queryset = self.filter_queryset(queryset)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is None:
            serializer = serializers.SeriesListSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = serializers.SeriesListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
