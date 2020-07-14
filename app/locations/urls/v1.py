from django.urls import path, include
from rest_framework import routers

from locations import public_views
from locations import views

app_name = 'locations'

router = routers.SimpleRouter()
router.register('city', views.CityViewSet, base_name='city')

public_router = routers.SimpleRouter()
public_router.register('city', public_views.CityViewSet)

public_url_patterns = [
    path('', include(public_router.urls)),
]

urlpatterns = [
    path('', include(router.urls)),
    path('public/', include(public_url_patterns))
]
