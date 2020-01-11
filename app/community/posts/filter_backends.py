from rest_framework.filters import BaseFilterBackend
import coreapi

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
            )
        ]

    def filter_queryset(self, request, queryset, *args, **kwargs):
        if not request.query_params.get('tag'):
            return queryset

        if 'following' == request.query_params['tag']:
            following = Following.objects.filter(follower=request.user).values_list('followed', flat=True)
            return queryset.filter(creator__in=following)
        return queryset.filter(creator__profile__tags=request.query_params['tag'])


class BlockersFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, *args, **kwargs):
        blocking = Block.objects.filter(blocker=request.user).values_list('blocked', flat=True)
        return queryset.exclude(creator__in=blocking)
