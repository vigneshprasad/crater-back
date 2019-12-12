from rest_framework.filters import BaseFilterBackend
import coreapi

from community.groups.models import Following, Block


class FollowingFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [
            coreapi.Field(
                name='type',
                location='query',
                required=False,
                type='string',
                description='Filter by following'
            )
        ]

    def filter_queryset(self, request, queryset, *args, **kwargs):
        if 'following' in request.query_params:
            following = Following.objects.filter(follower=request.user).values_list('followed', flat=True)
            return queryset.filter(creator__in=following)
        return queryset


class BlockersFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, *args, **kwargs):
        blocking = Block.objects.filter(blocker=request.user).values_list('blocked', flat=True)
        return queryset.exclude(creator__in=blocking)
