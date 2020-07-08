from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from community.comments.paginators import CommentPagination
from community.comments.serializers import CommentSerializer
from community.comments.services import get_comments
from community.comments.models import Comment
from community.posts.models import Post
from community.posts.services import get_post
from users import permissions


class CommentViewSet(mixins.CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = CommentSerializer
    queryset = get_comments()
    pagination_class = CommentPagination
    permission_classes = (permissions.IsAuthenticated,)

    @action(
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def post(self, request, pk):
        offset = int(request.query_params.get('offset', 2))
        try:
            post = get_post(pk)
            queryset = self.filter_queryset(post.comments.all()[offset:])
            # Sorting the outgoing comments in order of creation.
            queryset = sorted(queryset, key=lambda x: x.created)
        except (Comment.DoesNotExist, Post.DoesNotExist):
            raise NotFound
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
