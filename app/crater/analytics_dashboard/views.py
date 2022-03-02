import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Count, F
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from users import permissions as user_permissions
from conversations import models as conversations_models
from conversations import services as conversations_services
from conversations import constants as conversations_constants
from crater.creator import private as creator_private
from crater.analytics_dashboard import serializers


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

        # Get follower count for user
        follower_count = creator_private.get_follower_count(
            user=user
        )

        response = {"count": follower_count}

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def follower_growth(self, request):
        user = request.user
        now = datetime.datetime.now()

        percentage_growth = conversations_services.get_rsvp_growth_over_month(
            user=user,
            created_at=now
        )

        response = {"percentage": percentage_growth}

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def average_engagement(self, request):
        user = request.user

        average_engagement = conversations_services.get_average_engagement(
            user=user
        )

        response = {"count": average_engagement}

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
        serializer_class=serializers.TopStreamsSerializer
    )
    def top_streams(self, request):
        user = request.user

        top_streams = conversations_services.get_top_streams_of_creator(
            user=user,
            count=3
        )

        serializer = self.get_serializer(top_streams, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def club_members_growth(self, request):
        user = request.user
        now = datetime.datetime.now()
        last_year = now.replace(day=1) - relativedelta(years=1)

        rsvp_count_by_month_and_year = conversations_services.get_rsvp_count_by_month_and_year(
            user=user,
            start_datetime=last_year,
            end_datetime=now
        )

        return Response(rsvp_count_by_month_and_year, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def conversion_funnel(self, request):
        user = request.user

        # Get all RSVPs for creator's streams
        rsvps = conversations_services.get_rsvps_for_creator_streams(
            user=user
        )

        rsvp_count = rsvps.count()

        # Get total recurring users for creator's streams
        recurring_user_count = conversations_services.get_users_by_number_of_rsvps(
            requests=rsvps,
            num=2
        )

        # Get total follower count for creator
        follower_count = conversations_services.get_users_by_number_of_rsvps(
            requests=rsvps,
            num=1
        )

        recurring_user_percentage = round(recurring_user_count / follower_count * 100, 2)

        # Get total subscribers for creator
        subscriber_count = creator_private.get_subscriber_count(
            user=user
        )

        subscriber_percentage = round(subscriber_count / follower_count * 100, 2)

        response = [
            {
                "name": "RSVP",
                "value": rsvp_count
            },
            {
                "name": "Subscribers",
                "value": subscriber_percentage
            },
            {
                "name": "Recurring Users",
                "value": recurring_user_percentage
            }
        ]

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def comparative_engagement(self, request):
        user = request.user

        comparative_engagement = conversations_services.get_comparative_engagement_of_creator(
            user=user
        )

        response = {"percentage": comparative_engagement}

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
        serializer_class=serializers.ComparativeRankingSerializer
    )
    def comparative_ranking(self, request):
        user = request.user
        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=30)

        top_creators, my_rank = creator_private.get_top_creators_by_date_range(
            start_date=start_date,
            end_date=end_date,
            count=3,
            user=user
        )

        # Filter creator's best stream based on number of number of
        # RSVPs and messages
        for data in top_creators:
            best_stream = conversations_models.Group.objects.filter(
                type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM,
                is_published=True,
                is_live=False,
                closed=True,
                host=data["pk"],
                start__range=[start_date, end_date]
            ).values(
                "id",
                "start",
                topic_title=F("topic__name"),
                topic_image=F("topic__image")
            ).annotate(
                rsvp_count=Count("requests", distinct=True)
            ).annotate(
                messages_count=Count("group_questions", distinct=True)
            ).order_by(
                "-rsvp_count", "-messages_count"
            ).first()

            if best_stream:
                data["stream_id"] = best_stream.get("id")
                data["stream_topic"] = best_stream.get("topic_title")
                data["stream_image"] = best_stream.get("topic_image")
                data["stream_date"] = best_stream.get("start")

        serializer = self.get_serializer(top_creators, many=True)

        response = {
            "rank": my_rank,
            "creator_ranking": serializer.data
        }

        return Response(response, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def traffic_source_types(self, request):
        user = request.user

        traffic_source_data = creator_private.get_traffic_sources_for_creator(
            user=user
        )

        return Response(traffic_source_data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False
    )
    def users_by_crater(self, request):
        user = request.user

        percentage = creator_private.get_percentage_creator_followers_from_crater(
            user=user
        )

        response = {"percentage": percentage}

        return Response(response, status=status.HTTP_200_OK)
