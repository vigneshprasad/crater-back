from django.urls import path, include
from rest_framework import routers

from creative_exchange import views

app_name = 'creative_exchange'

router = routers.SimpleRouter()
router.register('categories', views.ExchangeCategoryViewSet, base_name='category')

urlpatterns = [
    path('', include(router.urls))
]
