from django.urls import path, include

urlpatterns = [
    path("agora/", include("integrations.agora.urls.v1")),
    path("dyte/", include("integrations.dyte.urls.v1"))
]
