from django.urls import path, include
from rest_framework.routers import DefaultRouter

from points.views import UserPointsViewSet, PointsRuleViewSet

app_name = 'points'

router = DefaultRouter()
router.register('', UserPointsViewSet)
router.register('rules', PointsRuleViewSet, base_name='points-rules')

urlpatterns = [
  path('', include(router.urls))
]