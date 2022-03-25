from django.urls import path, include
from rest_framework import routers

from conversations.dashboard import views

app_name = "dashboard"

router = routers.SimpleRouter()

router.register("user", views.UserCreateSearchViewSet, base_name="user_create_search")
router.register("webinar", views.CreateUpdateWebinarViewSet, base_name="create_update_webinar_view")
router.register("category", views.CategoryViewSet, base_name="dashboard_category_viewset")


urlpatterns = [
    path("", include(router.urls))
]
