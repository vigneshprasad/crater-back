from django.urls import path, include
from rest_framework import routers

from locations import views

app_name = 'locations'

router = routers.SimpleRouter()
router.register('city', views.CityViewSet, base_name='city')

urlpatterns = [
    path('', include(router.urls))
]
