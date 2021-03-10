from django.urls import path, include

urlpatterns = [
    path('agora/', include('integrations.agora.urls.v1'))
]