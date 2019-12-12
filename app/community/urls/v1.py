from django.urls import path, include
from rest_framework.routers import DefaultRouter

from community.comments.views import CommentViewSet
from community.groups.views import UserGroupViewSet, BlockViewSet
from community.posts.views import PostViewSet, LikeViewSet

app_name = 'community'

router = DefaultRouter()
router.register('posts', PostViewSet)
router.register('groups', UserGroupViewSet),
router.register('comments', CommentViewSet),
router.register('likes', LikeViewSet),
router.register('blockers', BlockViewSet),


urlpatterns = [
    path('', include(router.urls)),
]
