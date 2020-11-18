from django.urls import path, include
from rest_framework.routers import SimpleRouter

from rewards import views

app_name = 'rewards'

router = SimpleRouter()

router.register('package', views.PackagesViewSet, base_name='packages')

urlpatterns = [
    path('', include(router.urls)),
    path('package/request', views.PackageRequestViewSet.as_view(), name='package-request')
]
