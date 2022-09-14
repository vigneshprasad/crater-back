import datetime

from rest_framework import filters

from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin


from conversations import serializers as conversations_serializers
from conversations import models as conversations_models
from conversations import constants as conversations_constants
from crater.creator import models as creator_models
from crater.creator import serializers as creator_serializers
from users import permissions as user_permissions
from crater.search import paginators


class UpcomingStreamsSearchViewSet(
    ListModelMixin,
    GenericViewSet
):
    serializer_class = conversations_serializers.StreamListSerializer
    queryset = conversations_models.Group.objects.filter(
        type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM,
        is_published=True,
        is_live=False,
        closed=False,
        start__gte=datetime.datetime.now()
    ).select_related(
        "topic",
        "host",
        "host__profile",
    )
    permission_classes = [user_permissions.AllowAny]
    filter_backends = (filters.SearchFilter,)
    search_fields = ["topic__name"]
    pagination_class = paginators.SearchPagination


class PastStreamsSearchViewSet(
    ListModelMixin,
    GenericViewSet
):
    serializer_class = conversations_serializers.StreamListSerializer
    queryset = conversations_models.Group.objects.filter(
        type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM,
        is_published=True,
        is_live=False,
        closed=True,
        start__lte=datetime.datetime.now()
    ).select_related(
        "topic",
        "host",
        "host__profile"
    )
    permission_classes = [user_permissions.AllowAny]
    filter_backends = (filters.SearchFilter,)
    search_fields = ["topic__name"]
    pagination_class = paginators.SearchPagination


class CreatorSearchViewSet(
    ListModelMixin,
    GenericViewSet
):
    serializer_class = creator_serializers.CreatorListSerializer
    queryset = creator_models.Creator.objects.filter(
        is_active=True
    ).select_related(
        "user",
        "user__profile"
    )
    permission_classes = [user_permissions.AllowAny]
    filter_backends = (filters.SearchFilter,)
    search_fields = ["user__name"]
    pagination_class = paginators.SearchPagination


class CategorySearchViewSet(
    ListModelMixin,
    GenericViewSet
):
    serializer_class = conversations_serializers.CategorySerializer
    queryset = conversations_models.Category.objects.filter(
        is_active=True
    )
    permission_classes = [user_permissions.AllowAny]
    filter_backends = (filters.SearchFilter,)
    search_fields = ["name"]
