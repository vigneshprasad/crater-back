from django.urls import path, include
from rest_framework.routers import DefaultRouter

from community.comments.views import CommentViewSet
from community.groups.views import UserRequestViewSet, BlockViewSet, FollowViewSet
from community.posts.views import PostViewSet, LikeViewSet, ReportViewSet

app_name = 'community'

router = DefaultRouter()
router.register('posts', PostViewSet)
router.register('requests', UserRequestViewSet),
router.register('comments', CommentViewSet),
router.register('likes', LikeViewSet),
router.register('reports', ReportViewSet),
router.register('blocks', BlockViewSet),
router.register('follows', FollowViewSet),


urlpatterns = [
    path('', include(router.urls)),
]
