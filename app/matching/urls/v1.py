from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

from matching import public_views


app_name = 'matching'

# All the public patterns will go here.
public_router = DefaultRouter()
public_router.register('matches', public_views.TopMatchesPublicViewSet)

# All the public patterns will go here.
public_url_patterns = []

urlpatterns = [
    path('public/', include(public_router.urls))
]
