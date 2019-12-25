from django.urls import path, include
from rest_framework import routers

from services import views

app_name = 'services'

router = routers.SimpleRouter()
router.register('category', views.CategoryViewSet)
router.register('user-service', views.ServiceViewSet, base_name='user-service')

urlpatterns = [
    path('', include(router.urls))
]
