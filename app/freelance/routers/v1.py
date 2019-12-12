from django.urls import path, include

app_name = 'v1'

urlpatterns = [
    path('user/', include('users.urls.v1', namespace='users')),
    path('locations/', include('locations.urls.v1', namespace='locations')),
    path('tags/', include('tags.urls.v1', namespace='tags'))
]
