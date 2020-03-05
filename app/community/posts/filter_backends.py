import coreapi
from rest_framework.filters import BaseFilterBackend

from community.groups.models import Following, Block


class FollowingFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [
            coreapi.Field(
                name='tag',
                location='query',
                required=False,
                type='string',
                description='Filter Posts'
            ),
            coreapi.Field(
                name='following',
                location='query',
                required=False,
                type='boolean',
                description='Filter Posts by following'
            )
        ]

    def filter_queryset(self, request, queryset, *args, **kwargs):
        tag = request.query_params.get('tag')
        if 'following' == tag or request.query_params.get('following') == 'true':
            following = Following.objects.filter(follower=request.user).values_list('followed', flat=True)
            queryset = queryset.filter(creator__in=following)
        if tag and tag != 'following':
            queryset = queryset.filter(creator__profile__tags=tag)
        return queryset.distinct()


class BlockersFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, *args, **kwargs):
        blocking = Block.objects.filter(blocker=request.user).values_list('blocked', flat=True)
        return queryset.exclude(creator__in=blocking)


class UserTagFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [
            coreapi.Field(
                name='tags',
                location='query',
                required=False,
                type='string',
                description='Filter by user tag'
            ),
        ]

    def filter_queryset(self, request, queryset, *args, **kwargs):
        tags = request.query_params.get('tags')
        try:
            if tags:
                queryset = queryset.filter(creator__profile__tags__in=tags.split(','))
        except (ValueError, TypeError):
            return queryset.none()
        return queryset
