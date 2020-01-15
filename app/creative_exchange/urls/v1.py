from django.urls import path, include
from rest_framework import routers

from creative_exchange import views

app_name = 'creative_exchange'

router = routers.SimpleRouter()
router.register('categories', views.ExchangeCategoryViewSet, base_name='category')
router.register('request/quote', views.MyRequestsQuotesViewSet, base_name='request-quote')
router.register('request', views.ExchangeRequestViewSet, base_name='request')
router.register('quote', views.ExchangeQuoteViewSet, base_name='quote')

urlpatterns = [
    path('', include(router.urls))
]
