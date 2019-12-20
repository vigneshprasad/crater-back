from django.urls import path, include
from rest_framework import routers

from users import social_views
from .. import views

app_name = 'users'

register_router = routers.SimpleRouter()
register_router.register('profile', views.ProfileViewSet, base_name='profile')
register_router.register('bank_details', views.BankDetailViewSet, base_name='bank-details')
register_router.register('verify', views.VerificationView, base_name='verify')

auth_urlpatterns = [

    path('logout/', views.LogoutView.as_view(), name='rest_logout'),
    path('', include('rest_auth.urls')),

    path('registration/', include('rest_auth.registration.urls')),
    path('', include(register_router.urls)),

    path('social/facebook/', social_views.FacebookLogin.as_view(), name='fb_login'),
    path('social/facebook/connect/', social_views.FacebookConnect.as_view(), name='fb_connect'),

    path('social/linkedin/', social_views.LinkedinLogin.as_view(), name='linkedin_login'),
    path('social/linkedin/connect/', social_views.LinkedinConnect.as_view(), name='linkedin_connect'),

    path('social/google/', social_views.GoogleLogin.as_view(), name='google_login'),
    path('social/google/connect/', social_views.GoogleConnect.as_view(), name='google_connect'),

    path('social/accounts/', social_views.SocialAccountListView.as_view(), name='social_account_list'),
    path('social/accounts/<int:pk>/disconnect/',
         social_views.SocialAccountDisconnectView.as_view(),
         name='social_account_disconnect'),

    path('network/', views.NetworkView.as_view(), name='network'),

]

urlpatterns = [
    path('auth/', include(auth_urlpatterns))
]
