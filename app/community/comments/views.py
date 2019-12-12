from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from community.comments.paginators import CommentPagination
from community.comments.serializers import CommentSerializer
from community.comments.services import get_comments_without_latest


class CommentViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):
    serializer_class = CommentSerializer
    queryset = get_comments_without_latest()
    pagination_class = CommentPagination
    permission_classes = (IsAuthenticated,)
