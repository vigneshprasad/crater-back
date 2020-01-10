from django.urls import path, include
from rest_framework import routers

from creative_exchange import views

app_name = 'creative_exchange'

router = routers.SimpleRouter()
router.register('categories', views.ExchangeCategoryViewSet, base_name='category')
router.register('request', views.ExchangeRequestViewSet, base_name='request')

urlpatterns = [
    path('', include(router.urls))
]
