from django.urls import path, include
from rest_framework import routers

from tags import views

app_name = 'tags'

router = routers.SimpleRouter()
router.register('city', views.TagViewSet, base_name='tag')

urlpatterns = [
    path('', include(router.urls))
]
