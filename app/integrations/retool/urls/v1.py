from django.urls import path, include
from rest_framework import routers

from integrations.retool import views


app_name = "retool"

router = routers.SimpleRouter()

router.register("data", views.RetoolDataViewSet, base_name="retool_data")

urlpatterns = [
    path("", include(router.urls))
]
