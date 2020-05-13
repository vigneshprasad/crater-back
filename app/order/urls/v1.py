from django.urls import path, include
from rest_framework import routers

from order import views

app_name = 'order'

router = routers.SimpleRouter()
router.register('buyer', views.BuyerOrderViewSet, base_name='order-buyer')
router.register('seller', views.SellerOrderViewSet, base_name='order-seller')
router.register('cart', views.CartOrderViewSet, base_name='order-cart')
router.register('quote/buyer', views.BuyerQuoteViewSet, base_name='quote-buyer')
router.register('quote/seller', views.SellerQuoteViewSet, base_name='quote-seller')
router.register('funding_request/buyer', views.BuyerFundingRequestViewSet, base_name='funding-request-buyer')
router.register('funding_request/investor', views.InvestorFundingRequestViewSet, base_name='funding-request-investor')

urlpatterns = [
    path('', include(router.urls))
]
