from django.urls import path, include
from rest_framework.routers import DefaultRouter

from points.views import UserPointsViewSet

app_name = 'points'

router = DefaultRouter()
router.register('', UserPointsViewSet)

urlpatterns = [
  path('', include(router.urls))
]