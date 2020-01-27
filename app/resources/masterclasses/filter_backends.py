from rest_framework.filters import BaseFilterBackend
import coreapi


class TagFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [
            coreapi.Field(
                name='tags',
                location='query',
                required=False,
                type='string',
                description='Filter by tags'
            ),
        ]

    def filter_queryset(self, request, queryset, *args, **kwargs):
        tags = request.query_params.get('tags')
        if tags:
            try:
                queryset = queryset.filter(tags__in=tags.split(','))
            except (ValueError, TypeError):
                return queryset.none()
        return queryset
