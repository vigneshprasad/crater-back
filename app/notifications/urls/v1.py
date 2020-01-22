from django.urls import path, include
from rest_framework import routers

from notifications import views

app_name = 'notifications'

router = routers.SimpleRouter()
router.register('settings', views.UserNotificationSettingsViesSet, base_name='user-settings')
router.register('my', views.NotificationViewSet, base_name='my')

urlpatterns = [
    path('', include(router.urls))
]
