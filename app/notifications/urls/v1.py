from django.urls import path, include
from rest_framework import routers

from notifications import views

app_name = 'notifications'

router = routers.SimpleRouter()
router.register('settings', views.UserNotificationSettings, base_name='user-settings')

urlpatterns = [
    path('', include(router.urls))
]
