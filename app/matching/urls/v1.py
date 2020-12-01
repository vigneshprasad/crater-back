from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

from matching import public_views


app_name = 'matching'

router = DefaultRouter()

# All the public patterns will go here.
public_router = DefaultRouter()
public_router.register('matches', public_views.TopMatchesPublicViewSet)

# All the public patterns will go here.
public_url_patterns = []

urlpatterns = [
    path('', include(router.urls)),
    # path('public/', include(public_url_patterns)),
    path('public/', include(public_router.urls))
]
