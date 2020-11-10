from django.urls import path, include
from rest_framework.routers import DefaultRouter

from rewards import views

app_name = 'rewards'

router = DefaultRouter()

router.register('package', views.PackagesViewSet, base_name='packages')
router.register('package/request', views.PackageRequestViewSet, base_name='package-requests')

urlpatterns = [
    path('', include(router.urls))
]
