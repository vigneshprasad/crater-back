from django.urls import path, include

app_name = 'v1'

urlpatterns = [
    path('user/', include('users.urls.v1', namespace='users')),
    path('locations/', include('locations.urls.v1', namespace='locations')),
    path('community/', include('community.urls.v1', namespace='community')),
    path('resources/', include('resources.urls.v1', namespace='resources')),
    path('tags/', include('tags.urls.v1', namespace='tags')),
    path('services/', include('services.urls.v1', namespace='services')),
    path('order/', include('order.urls.v1', namespace='orders')),
    path('creative-exchange/', include('creative_exchange.urls.v1', namespace='creative-exchange')),
]
