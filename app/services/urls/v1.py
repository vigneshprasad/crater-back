from django.urls import path, include
from rest_framework import routers

from services import public_views
from services import views

app_name = 'services'

router = routers.SimpleRouter()
router.register('category', views.CategoryViewSet)
router.register('professionals', views.ProfessionalsViewSet, base_name='professionals')
router.register('user_service', views.UserServicesViewSet, base_name='user-service')
router.register('investor_service', views.InvestorServicesViewSet, base_name='investor-service')

public_router = routers.SimpleRouter()
public_router.register('category', public_views.CategoryViewSet, basename='public_service_category')
public_router.register('professionals', public_views.ProfessionalsViewSet, basename='public_professional_service')
public_router.register('user', public_views.UserServicesViewSet, basename='public_user_service')
public_router.register('investor', public_views.InvestorServicesViewSet, basename='public_investor_service')

public_url_patterns = [
    path('', include(public_router.urls)),
]

urlpatterns = [
    path('', include(router.urls)),
    path('public/', include(public_url_patterns))
]
