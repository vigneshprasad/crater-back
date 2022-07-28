from django.urls import path, include

urlpatterns = [
    path("learn/", include("tokens.learn.urls.v1", namespace="learn")),
]
