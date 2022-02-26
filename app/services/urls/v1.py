from django.urls import path, include
from rest_framework import routers

from services import public_views
from services import views

app_name = 'services'

router = routers.SimpleRouter()
router.register('category', views.CategoryViewSet)

public_router = routers.SimpleRouter()
public_router.register('category', public_views.CategoryViewSet, basename='public_service_category')

public_url_patterns = [
    path('', include(public_router.urls)),
]

urlpatterns = [
    path('', include(router.urls)),
    path('public/', include(public_url_patterns))
]
