from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from community.groups.models import Group
from community.groups.permissions import GroupPermission, GroupPostPermission
from community.groups.services import get_group
from community.posts.filter_backends import FollowingFilterBackend, BlockersFilterBackend
from community.posts.models import Like, Report
from community.posts.paginators import PostPagination
from community.posts.permissions import PostPermission
from community.posts.serializers import PostSerializer, LikeSerializer, ReportSerializer
from community.posts.services import get_posts, get_likes, get_post


class PostViewSet(ModelViewSet):
    serializer_class = PostSerializer
    queryset = get_posts()
    pagination_class = PostPagination
    permission_classes = (IsAuthenticated, PostPermission)
    filter_backends = (FollowingFilterBackend, BlockersFilterBackend)

    @action(
        methods=['get'],
        permission_classes=[IsAuthenticated, GroupPermission],
        detail=True
    )
    def group(self, request, pk):
        try:
            group = get_group(pk=pk)
        except Group.DoesNotExist:
            raise NotFound
        context = self.get_serializer_context()
        return Response(self.serializer_class(group.posts.all(), many=True, **{'context': context}).data)


class LikeViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    serializer_class = LikeSerializer
    queryset = get_likes()
    permission_classes = (IsAuthenticated, GroupPostPermission)

    def destroy(self, request, *args, **kwargs):
        """
        Delete like by post id specified in url and request user
        """
        post = get_post(kwargs['pk'])
        try:
            Like.objects.get(post=post, user=request.user).delete()
        except Like.DoesNotExist:
            raise NotFound
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportViewSet(mixins.CreateModelMixin, GenericViewSet):
    serializer_class = ReportSerializer
    queryset = Report.objects.none()
    permission_classes = (IsAuthenticated, GroupPostPermission)
