from django.urls import path, include

app_name = 'v1'

urlpatterns = [
    path('user/', include('users.urls.v1', namespace='users')),
    path('locations/', include('locations.urls.v1', namespace='locations')),
    path('community/', include('community.urls.v1', namespace='community')),
]
