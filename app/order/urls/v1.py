from django.urls import path, include
from rest_framework import routers

from order import views

app_name = 'order'

router = routers.SimpleRouter()
router.register('buyer', views.OrderViewSet, base_name='buyer')
router.register('funding_request/buyer', views.FundingRequestViewSet, base_name='funding-request-buyer')

urlpatterns = [
    path('', include(router.urls))
]
