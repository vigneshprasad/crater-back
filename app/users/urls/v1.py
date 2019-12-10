from django.urls import path, include
from rest_auth.registration.views import (
    SocialAccountListView, SocialAccountDisconnectView
)
from rest_framework import routers
from users import social_views

app_name = 'usersS'

router = routers.SimpleRouter()

urlpatterns = [
    path('', include('rest_auth.urls')),
    path('registration/', include('rest_auth.registration.urls')),

    path('social/facebook/', social_views.FacebookLogin.as_view(), name='fb_login'),
    path('social/facebook/connect/', social_views.FacebookConnect.as_view(), name='fb_connect'),

    path('social/linkedin/', social_views.LinkedinLogin.as_view(), name='linkedin_login'),
    path('social/linkedin/connect/', social_views.LinkedinConnect.as_view(), name='linkedin_connect'),

    path('social/google/', social_views.GoogleLogin.as_view(), name='google_login'),
    path('social/google/connect/', social_views.GoogleConnect.as_view(), name='google_connect'),

    path('social/accounts/', SocialAccountListView.as_view(), name='social_account_list'),
    path('social/accounts/<int:pk>/disconnect/',
         SocialAccountDisconnectView.as_view(),
         name='social_account_disconnect'),
]
