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
from integrations.dyte import models as dyte_models
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
        start = now.replace(day=1) - relativedelta(months=4)

        follower_count_by_month_and_year = creator_private.get_follower_count_by_month_and_year(
            user=user,
            start=start,
            end=now
        )

        return Response(follower_count_by_month_and_year, status=status.HTTP_200_OK)

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

        recurring_user_percentage = round(recurring_user_count / follower_count * 100, 2) if follower_count > 0 else None

        # Get total subscribers for creator
        subscriber_count = creator_private.get_subscriber_count(
            user=user
        )

        subscriber_percentage = round(subscriber_count / follower_count * 100, 2) if follower_count > 0 else None

        response = {
            "total_rsvp": rsvp_count,
            "followers_percentage": subscriber_percentage,
            "recurring_users_percentage": recurring_user_percentage
        }

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

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[user_permissions.IsAuthenticatedOrReadOnly]
    )
    def platform_stats(self, request):
        # Get total creators
        total_creators = creator_private.get_total_creators()

        # Get total streams
        total_streams = conversations_services.get_past_streams().count()

        # Get total chat engagement
        chat_engagement = conversations_services.get_average_engagement()

        # Get total stream time
        total_stream_time = conversations_services.get_total_stream_time_for_creators()

        data = {
            "total_creators": total_creators + 600,
            "total_streams": total_streams,
            "chat_engagement": chat_engagement,
            "total_stream_time": total_stream_time
        }

        return Response(data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[user_permissions.IsAuthenticatedOrReadOnly]
    )
    def stream_category_distribution(self, request):
        stream_category_distribution = conversations_services.get_stream_category_distribution()

        return Response(stream_category_distribution, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False
    )
    def channel_stats(self, request):
        user = request.user

        # Get total stream time
        total_stream_time = conversations_services.get_total_stream_time_for_creator(user=user)

        # Get total streams
        total_streams = conversations_services.get_past_streams(user=user).count()

        # Get total subscribers
        total_followers = creator_private.get_subscriber_count(user=user)

        # Calculate average stream length
        if total_streams:
            average_stream_length = round(total_stream_time / total_streams, 2)
        else:
            average_stream_length = 0

        # Get average stream engagement
        average_stream_engagement = conversations_services.get_average_engagement(
            user=user
        )

        data = {
            "total_stream_time": total_stream_time,
            "total_streams": total_streams,
            "total_followers": total_followers,
            "average_stream_length": average_stream_length,
            "average_stream_engagement": average_stream_engagement
        }

        return Response(data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False
    )
    def stream_completion(self, request):
        user = request.user

        # Get recent 5 past streams of user
        past_streams = conversations_services.get_past_streams(user=user)[:5]
        if not past_streams:
            return Response([], status=status.HTTP_200_OK)

        # Get completion rate for streams
        stream_completion_data = conversations_services.get_completion_rate_for_streams(
            host=user,
            streams=past_streams
        )

        return Response(stream_completion_data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False
    )
    def stream_time(self, request):
        user = request.user
        today = datetime.datetime.now().date()

        # Check if the user has a past stream today
        past_streams = conversations_models.Group.objects.filter(
            type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM,
            is_published=True,
            is_live=False,
            closed=True,
            host=user,
            start__date=today
        )

        if not past_streams:
            time = datetime.time(0, 0)
            return Response({"time": time}, status=status.HTTP_200_OK)

        dyte_participants_for_host = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group__in=past_streams,
            participant_id=user,
            last_online_at__isnull=False
        )

        total_minutes = conversations_services.calculate_total_minutes_on_stream(
            dyte_participants=dyte_participants_for_host
        )

        time = datetime.time(total_minutes // 60, total_minutes % 60)

        return Response({"time": time}, status=status.HTTP_200_OK)
