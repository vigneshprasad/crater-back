import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Count, F, Value
from django.db.models.functions import Coalesce, Concat, TruncDate
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from users import permissions as user_permissions
from crater.creator import models as creator_models
from conversations import models as conversation_models
from conversations import constants as conversation_constants
from crater.analytics_dashboard import serializers
from django.conf import settings


class AnalyticsDashboardViewSet(
    mixins.ListModelMixin,
    GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]

    @action(
        methods=["get"],
        detail=False
    )
    def my_club(self, request):
        user = request.user

        # Get creator follower count
        followers_count = creator_models.Follower.objects.filter(
            creator__user=user,
            unfollowed=False
        ).count()

        response = {"count": followers_count}

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def follower_growth(self, request):
        user = request.user
        now = datetime.datetime.now()
        prev_month_date = now - relativedelta(months=1)

        follower_count_prev_month = creator_models.Follower.objects.filter(
            creator__user=user,
            unfollowed=False,
            followed_at__month=prev_month_date.month,
            followed_at__year=prev_month_date.year
        ).count()

        if not follower_count_prev_month:
            return Response({"percentage": 0}, status=status.HTTP_200_OK)

        follower_count_current_month = creator_models.Follower.objects.filter(
            creator__user=user,
            unfollowed=False,
            followed_at__month=now.month,
            followed_at__year=now.year
        ).count()

        percentage_growth = round(
            ((follower_count_current_month - follower_count_prev_month) / follower_count_prev_month) * 100,
            2
        )

        response = {"percentage": percentage_growth}

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def average_engagement(self, request):
        user = request.user
        now = datetime.datetime.now()

        # Filter creator's streams
        groups = conversation_models.Group.objects.filter(
            is_live=False,
            closed=True,
            start__lt=now,
            host=user
        )

        if groups:
            # Total count of messages from creator's streams
            total_messages = conversation_models.GroupMessage.objects.filter(
                group__host=user
            ).count()

            average_engagement = round(total_messages / groups.count())
        else:
            average_engagement = 0

        response = {"count": average_engagement}

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
        serializer_class=serializers.TopStreamsSerializer
    )
    def top_streams(self, request):
        user = request.user
        now = datetime.datetime.now()

        # Get top 3 creator's streams with total number of RSVPs and messages
        groups = conversation_models.Group.objects.filter(
            is_live=False,
            closed=True,
            start__lt=now,
            host=user
        ).values(
            "id",
            "start",
            topic_title=F("topic__name"),
            topic_image=Coalesce(Concat(
                Value(f"{settings.MEDIA_URL}"),
                F("topic__image")
            ), Value(None)),
        ).annotate(
            rsvp_count=Count("requests", distinct=True)
        ).annotate(
            messages_count=Count("group_questions", distinct=True)
        ).order_by(
            "-rsvp_count", "-messages_count"
        )[:3]

        serializer = self.get_serializer(groups, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def club_members_growth(self, request):
        user = request.user
        now = datetime.datetime.now()
        last_week = now - datetime.timedelta(weeks=1)

        follower_count_data = creator_models.Follower.objects.filter(
            creator__user=user,
            unfollowed=False,
            followed_at__date__gte=last_week
        ).values(
            followed_at_date=TruncDate(F("followed_at__date"))
        ).annotate(
            follower_count=Count("followed_at_date")
        )

        return Response(follower_count_data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def conversion_funnel(self, request):
        user = request.user

        # Get all RSVPs for creator's streams
        requests = conversation_models.Request.objects.filter(
            group__host=user,
            participant_type=conversation_constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM,
            status=conversation_constants.REQUEST_STATUS_ACCEPTED_ENUM
        )

        rsvp_count = requests.count()

        # Get total recurring users for creator's streams
        recurring_user_count = requests.values(
            "requester"
        ).annotate(
            requester_count=Count("requester")
        ).exclude(
            requester_count=1
        ).count()

        # Get total subscribers for creator
        subscriber_count = creator_models.Follower.objects.filter(
            creator__user=user,
            unfollowed=False,
            notify=True
        ).count()

        response = [
            {
                "name": "Total RSVPs",
                "count": rsvp_count
            },
            {
                "name": "Total Subscribers",
                "count": subscriber_count
            },
            {
                "name": "Total Recurring Users",
                "count": recurring_user_count
            }
        ]

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def comparative_engagement(self, request):
        user = request.user
        now = datetime.datetime.now()

        # Filter all past streams
        groups = conversation_models.Group.objects.filter(
            is_live=False,
            closed=True,
            start__lt=now
        )

        if not groups:
            return Response({"percentage": 0}, status=status.HTTP_200_OK)

        group_ids = groups.values_list("id", flat=True)

        # Total count of messages from all streams
        total_messages_all_streams = conversation_models.GroupMessage.objects.filter(
            group__in=group_ids
        ).count()

        if not total_messages_all_streams:
            return Response({"percentage": 0}, status=status.HTTP_200_OK)

        average_engagement_all_streams = round(total_messages_all_streams / groups.count())

        # Filter creator's streams
        creator_groups = groups.filter(host=user)

        if not creator_groups:
            return Response({"comparative_engagement": 0}, status=status.HTTP_200_OK)

        # Total count of messages from creator's streams
        total_messages_creator_streams = conversation_models.GroupMessage.objects.filter(
            group__host=user
        ).count()

        average_engagement_creator_streams = round(total_messages_creator_streams / creator_groups.count())

        comparative_engagement = round(
            ((
                     average_engagement_creator_streams - average_engagement_all_streams) /
             average_engagement_all_streams) * 100,
            2
        )

        response = {"percentage": comparative_engagement}

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def comparative_ranking(self, request):
        now = datetime.datetime.now()

        # Filter top 5 creators with large follower count for current month
        ranking_data = creator_models.Follower.objects.filter(
            followed_at__month=now.month,
            followed_at__year=now.year
        ).values(
            creator_user_pk=F("creator__user"),
            creator_name=F("creator__user__name"),
            creator_image=Coalesce(Concat(
                Value(f"{settings.MEDIA_URL}"),
                F("creator__user__profile__photo")
            ), Value(None))
        ).annotate(
            follower_count=Count("id", distinct=True)
        ).order_by(
            "-follower_count"
        )[:3]

        # Filter creator's best stream based on number of RSVPs and messages
        for data in ranking_data:
            best_stream = conversation_models.Group.objects.filter(
                is_live=False,
                closed=True,
                host=data["creator_user_pk"]
            ).values(
                topic_title=F("topic__name")
            ).annotate(
                rsvp_count=Count("requests", distinct=True)
            ).annotate(
                messages_count=Count("group_questions", distinct=True)
            ).order_by(
                "-rsvp_count", "-messages_count"
            ).first()

            if best_stream:
                data["stream_topic"] = best_stream.get("topic_title")
            else:
                data["stream_topic"] = ""

        return Response(ranking_data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def traffic_source_types(self, request):
        user = request.user
        now = datetime.datetime.now()

        # Filter followers by user sources for current month
        traffic_source_data = creator_models.Follower.objects.filter(
            creator__user=user,
            unfollowed=False,
            followed_at__month=now.month,
            followed_at__year=now.year
        ).values(
            source_name=Coalesce(F("user__user_source__utm_source"), Value("Crater"))
        ).annotate(
            count=Count("id", distinct=True)
        )

        return Response(traffic_source_data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def crater_users(self, request):
        pass
