from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from twitter.error import TwitterError

from community.groups.models import Group
from community.groups.permissions import GroupPermission, GroupPostPermission
from community.groups.services import get_group, get_followers_count
from community.posts.filter_backends import FollowingFilterBackend, BlockersFilterBackend, UserTagFilterBackend
from community.posts.models import Like, Report
from community.posts.paginators import PostPagination
from community.posts.permissions import PostPermission
from community.posts.serializers import PostSerializer, LikeSerializer, ReportSerializer, LimitedPostSerializer
from community.posts.services import get_posts, get_likes, get_post, get_community_posts, get_my_posts
from order.serializers import EmptySerializer
from resources.curated_articles.services import get_company_curated_articles_data
from resources.events.services import get_first_event_data
from resources.masterclasses.services import get_first_masterclass_data
from users.models import User
from utils.twitter_service import api as twitter_api


class PostViewSet(ModelViewSet):
    serializer_class = PostSerializer
    queryset = get_community_posts()
    pagination_class = PostPagination
    permission_classes = (IsAuthenticated, PostPermission)
    filter_backends = (FollowingFilterBackend, BlockersFilterBackend, UserTagFilterBackend)

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

    @action(
        methods=['get'], permission_classes=[IsAuthenticated], detail=False, pagination_class=None, filter_backends=None
    )
    def company(self, request):
        return Response({
            'event': get_first_event_data(),
            'masterclass':  get_first_masterclass_data(),
            'articles': get_company_curated_articles_data(),
        })

    @action(methods=['get'], permission_classes=[IsAuthenticated], detail=True, filter_backends=None,
            serializer_class=LimitedPostSerializer, queryset=get_posts())
    def all(self, request, pk):
        context = self.get_serializer_context()
        profile_posts = get_my_posts(pk)
        page = self.paginate_queryset(profile_posts)
        serializer = self.get_serializer(page, many=True, context=context)

        return Response({
            'count': profile_posts.count(),
            'followers': get_followers_count(pk),
            'posts': serializer.data,
        })

    @action(methods=['get'], permission_classes=[IsAuthenticated], detail=True, filter_backends=None,
            serializer_class=EmptySerializer, queryset=User.objects.all())
    def twitter(self, request, pk):
        data = []
        try:
            u = User.objects.get(pk=pk)
            if u.has_profile and u.profile.twitter:
                try:
                    data = twitter_api.GetUserTimeline(screen_name=u.profile.twitter, count=20)
                except TwitterError:
                    pass
        except User.DoesNotExist:
            raise NotFound()
        return Response(data=[d._json for d in data])


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
