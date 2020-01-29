from django.urls import path, include
from rest_framework import routers

from .. import views

app_name = 'payment'

router = routers.SimpleRouter()
router.register('transactions', views.TransactionViewSet, base_name='transactions')

urlpatterns = [
    path('', include(router.urls))
]
