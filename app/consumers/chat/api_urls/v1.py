from django.urls import path, include
from rest_framework.routers import DefaultRouter

from consumers.chat.views import MessageViewSet

app_name = 'chat'

router = DefaultRouter()
router.register('message', MessageViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
