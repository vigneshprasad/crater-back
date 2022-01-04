import csv

from django.contrib.auth import get_user_model
from django.db.models import F
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, filters
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.creator import exceptions
from crater.creator import models
from crater.creator import paginators
from crater.creator import private
from crater.creator import serializers
from crater.creator import signals
from users import permissions as user_permissions


class CreatorViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.CreatorSerializer
    pagination_class = paginators.CreatorPagination
    queryset = models.Creator.objects.filter(is_active=True).order_by("-order", "created_at")
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    # We can get both certified and non-certified creators
    # with the same list call with different filterset fields.
    filterset_fields = ["certified"]
    search_fields = ["user__phone_number"]

    @action(
        methods=["get"],
        serializer_class=serializers.CreatorSerializer,
        pagination_class=paginators.CreatorPagination,
        permission_classes=user_permissions.IsAuthenticated,
        detail=False
    )
    def my(self, request, *args, **kwargs):
        """Returns paginated list of creators followed by the
            requesting user.

        """
        user = request.user

        followed_creator_ids = user.following.filter(unfollowed=False).values_list("creator", flat=True)
        followed_creators = self.get_queryset().filter(id__in=followed_creator_ids)

        page = self.paginate_queryset(followed_creators)

        if page is None:
            serializer = self.get_serializer(followed_creators, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["get"],
        serializer_class=serializers.CreatorSerializer,
        permission_classes=(user_permissions.IsAuthenticated,),
        detail=False
    )
    def me(self, request):
        """Returns the creator instance for the requested
            user if it exists.
        """
        try:
            creator = self.get_queryset().get(user=request.user)
        except models.Creator.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(creator)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False
    )
    def with_coins(self, request, *args, **kwargs):
        queryset = self.get_queryset().exclude(coin=None)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreatorSlugViewSet(
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.CreatorSerializer
    pagination_class = paginators.CreatorPagination
    queryset = models.Creator.objects.filter(is_active=True).order_by("-order")
    lookup_field = "slug"


class CommunityViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    serializer_class = serializers.CommunitySerializer
    pagination_class = paginators.CommunityPagination
    # All followers of the creator.
    queryset = models.Community.objects.filter(is_active=True)
    filterset_fields = ["creator"]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["get"],
        permission_classes=[user_permissions.AllowAny],
        serializer_class=serializers.CommunitySerializer,
        pagination_class=paginators.CommunityPagination,
        detail=False
    )
    def owned(self, request, *args, **kwargs):
        """Returns communities owned by a creator.

        Note:
            It's a public API for now. We can change it to
                authenticated API later.

        """
        user_pk = kwargs.get("pk")
        try:
            user = get_user_model().objects.get(pk=user_pk)
        except get_user_model().DoesNotExist:
            return self.generate_bad_request(
                {"error": "User does not exist."}
            )

        try:
            creator = models.Creator.objects.get(user=user)
        except models.Creator.DoesNotExist:
            return self.generate_bad_request(
                {"error": "User is not a creator."}
            )

        creator_communities = creator.communities_owned.all()
        serializer = self.get_serializer(creator_communities, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=["get"],
        permission_classes=[user_permissions.AllowAny],
        serializer_class=serializers.CommunitySerializer,
        pagination_class=paginators.CommunityPagination,
        detail=False
    )
    def joined(self, request, *args, **kwargs):
        """Returns communities joined by a user.

        Note:
            It's a public API for now. We can change it to
                authenticated API later.

        """
        user_pk = kwargs.get("pk")
        try:
            user = get_user_model().objects.get(pk=user_pk)
        except get_user_model().DoesNotExist:
            return self.generate_bad_request(
                {"error": "User does not exist."}
            )

        user_communities = user.communities_joined.all()
        serializer = self.get_serializer(user_communities, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class CommunityMemberViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.CommunityMemberSerializer
    pagination_class = paginators.CommunityMemberPagination
    # All followers of the creator.
    queryset = models.CommunityMember.objects.filter(
        is_active=True
    )
    filterset_fields = ["community"]

    @action(
        methods=["POST"],
        permission_classes=[user_permissions.IsAuthenticated],
        serializer_class=serializers.CommunityMemberSerializer,
        pagination_class=paginators.CommunityMemberPagination,
        detail=False
    )
    def join(self, request, *args, **kwargs):
        """Endpoint for joining a creator community."""
        user = request.user
        community_id = request.data.get("community")
        community_member = private.get_member_for_user_and_community_id(user, community_id)

        if not community_member:
            # If not community member is not found, create one.
            data = {
                "user": user.pk,
                "community": community_id,
                "joined_at": timezone.now(),
                "is_active": True
            }
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        if community_member.is_active:
            # If the community member object is already active.
            # throw an exception.
            community_already_joined = exceptions.CommunityAlreadyJoined()
            return Response(
                community_already_joined.get_error_body(),
                status=community_already_joined.status_code
            )

        data = {
            "user": user.pk,
            "community": community_id,
            "is_active": True
        }
        serializer = self.get_serializer(data, community_member, partial=True)
        serializer.is_valid(raise_exceptions=True)
        self.perform_update(serializer)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=["POST"],
        permission_classes=[user_permissions.IsAuthenticated],
        serializer_class=serializers.CommunityMemberSerializer,
        pagination_class=paginators.CommunityMemberPagination,
        detail=False
    )
    def leave(self, request, *args, **kwargs):
        """Endpoint for leave a creator community."""
        user = request.user
        community_id = kwargs.get("community")
        community_member = private.get_member_for_user_and_community_id(user, community_id)

        if not community_member or (community_member and not community_member.is_active):
            # If there is no community member or if the community member is.
            # already inactive, throw an exception.
            community_already_left_exception = exceptions.CommunityAlreadyLeft()
            return Response(
                community_already_left_exception.get_error_body(),
                status=community_already_left_exception.status_code
            )

        data = {
            "user": user.pk,
            "community": community_id,
            "is_active": False
        }
        serializer = self.get_serializer(data, community_member, partial=True)
        serializer.is_valid(raise_exceptions=True)
        self.perform_update(serializer)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class FollowerViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    serializer_class = serializers.FollowerSerializer
    pagination_class = paginators.FollowerPagination
    # All followers of the creator.
    queryset = models.Follower.objects.filter(unfollowed=False)
    filterset_fields = ["creator", "creator__user", "user"]

    @action(
        methods=["post"],
        serializer_class=serializers.FollowerSerializer,
        detail=False
    )
    def follow(self, request, *args, **kwargs):
        user = request.user
        creator_id = request.data.get("creator")

        follower = private.get_follower_for_user_and_creator_id(user, creator_id)

        # If the user already has a follower object and is not unfollowed
        # throw and exception.
        if follower and not follower.unfollowed:
            creator_already_followed_exception = exceptions.CreatorAlreadyFollowed()
            return Response(
                creator_already_followed_exception.get_error_body(),
                status=creator_already_followed_exception.status_code
            )

        # Perform update using the serializer.
        data = {
            "user": user.pk,
            "creator": creator_id,
            "unfollowed": False,
            "followed_at": timezone.now()
        }

        # Get update or create serializer based on if the user has a follower object.
        if follower:
            serializer = self.get_serializer(data=data, instance=follower, partial=True)
            serializer.is_valid(raise_exception=True)
        else:
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)

        # Update or create the follower.
        follower = serializer.save()

        # Send signals that the creator is unfollowed.
        signals.creator_followed.send(
            sender=follower.__class__,
            follower=follower
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=["post"],
        serializer_class=serializers.FollowerSerializer,
        detail=False
    )
    def unfollow(self, request, *args, **kwargs):
        user = request.user
        creator_id = kwargs.get("creator")

        follower = private.get_follower_for_user_and_creator_id(user, creator_id)

        # If the user has never followed the creator, throw an exception.
        if not follower:
            user_not_following_creator_exception = exceptions.UserNotFollowingCreator()
            return Response(
                user_not_following_creator_exception.get_error_body(),
                status=user_not_following_creator_exception.status_code
            )

        # If the user has already unfollowed the creator throw and exception.
        if follower.unfollowed:
            creator_already_unfollowed_exception = exceptions.CreatorAlreadyUnFollowed()
            return Response(
                creator_already_unfollowed_exception.get_error_body(),
                status=creator_already_unfollowed_exception.status_code
            )

        # Perform update using the serializer.
        data = {
            "user": user.pk,
            "creator": creator_id,
            "unfollowed": True,
            "unfollowed_at": timezone.now()
        }
        serializer = self.get_serializer(data=data, instance=follower, partial=True)
        serializer.is_valid(raise_exception=True)
        follower = serializer.save()

        # Send signals that the creator is unfollowed.
        signals.creator_unfollowed(
            sender=follower.__class__,
            follower=follower
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=["post"],
        serializer_class=serializers.FollowerSerializer,
        detail=False
    )
    def notify(self, request, *args, **kwargs):
        """Marks the follower object to notify for further
            livestreams from the creator.

        """

        user = request.user
        # TODO(Nishant): Discuss if we need webinar id here.
        creator_id = request.data.get("creator")

        # Get follower object for the user and creator.
        follower = private.get_follower_for_user_and_creator_id(
            user,
            creator_id
        )

        if follower:
            data = {
                "notify": True
            }
            serializer = self.get_serializer(data=data, instance=follower, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            created = False
        else:
            # Create follower object and turn notify on.
            data = {
                "user": user.pk,
                "creator": creator_id,
                "unfollowed": False,
                "notify": True,
                "followed_at": timezone.now()
            }
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            follower = serializer.save()
            created = True

        if created:
            # Send signals that the follower is created.
            signals.creator_followed.send(
                sender=follower.__class__,
                follower=follower
            )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=["GET"],
        detail=False,
    )
    def download_csv(self, request):
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="export.csv"'

        # Get all creator followers
        followers = models.Follower.objects.filter(
            creator__user=request.user,
            unfollowed=False
        ).values(name=F("user__name"), email=F("user__email"))

        writer = csv.DictWriter(
            response,
            fieldnames=["name", "email"]
        )
        writer.writeheader()
        writer.writerows(followers)

        return response


class CoinsViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.CoinSerializer
    queryset = models.Coin.objects.filter(is_active=True)

    @action(
        methods=["GET"],
        detail=True
    )
    def creator(self, request, pk, *args, **kwargs):
        try:
            coin_object = models.Coin.objects.get(creator=pk)
            serializer = self.get_serializer(coin_object)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (models.Coin.DoesNotExist, models.Coin.MultipleObjectsReturned):
            return Response(status=status.HTTP_404_NOT_FOUND)

