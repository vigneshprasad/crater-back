from django.urls import path, include
from rest_framework import routers

from services import views

app_name = 'services'

router = routers.SimpleRouter()
router.register('category', views.CategoryViewSet)
router.register('professionals', views.ProfessionalsViewSet, base_name='professionals')
router.register('user_service', views.UserServicesViewSet, base_name='user-service')
router.register('investor_service', views.InvestorServicesViewSet, base_name='investor-service')

urlpatterns = [
    path('', include(router.urls))
]
