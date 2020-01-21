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
                description='Filter by tag'
            ),
            coreapi.Field(
                name='website_tags',
                location='query',
                required=False,
                type='string',
                description='Filter by website tags'
            ),
        ]

    def filter_queryset(self, request, queryset, *args, **kwargs):
        tags = request.query_params.get('tags')
        website_tags = request.query_params.get('website_tags')
        try:
            if tags:
                queryset = queryset.filter(tag__in=tags.split(','))
            if website_tags:
                queryset = queryset.filter(website_tag__in=tags.split(','))
        except (ValueError, TypeError):
            return queryset.none()
        return queryset
