from django.urls import path, include
from rest_framework import routers

from users import public_views
from users import social_views
from .. import views

app_name = 'users'

register_router = routers.SimpleRouter()
register_router.register('profile/cover_file', views.CoverFileViewSet, base_name='profile-cover-file')
register_router.register('profile', views.ProfileViewSet, base_name='profile')
register_router.register('bank_details', views.BankDetailViewSet, base_name='bank-details')
register_router.register('verify', views.VerificationView, base_name='verify')
register_router.register('user_services', views.UserServicesViewSet, base_name='services')
register_router.register('investor_services', views.InvestorServicesViewSet, base_name='investor-services')

router = routers.SimpleRouter()
router.register('investors', views.InvestorsViewSet, base_name='investors')

# Router for Public API's.
public_router = routers.SimpleRouter()
public_router.register('investors', public_views.InvestorsViewSet, base_name='public-investors')
public_router.register('typeform_add_user', public_views.TypeFormViewSet, base_name='public-type-form-user')

public_urls_patterns = [
    path('', include(public_router.urls))
]

auth_urlpatterns = [

    path('logout/', views.LogoutView.as_view(), name='rest_logout'),
    path('', include('rest_auth.urls')),

    path('registration/verify-email/', views.VerifyEmailView.as_view(), name='rest_verify_email'),
    path('registration/', include('rest_auth.registration.urls')),
    path('', include(register_router.urls)),

    path('social/facebook/', social_views.FacebookLogin.as_view(), name='fb_login'),
    path('social/facebook/connect/', social_views.FacebookConnect.as_view(), name='fb_connect'),

    path('social/linkedin/', social_views.LinkedinLogin.as_view(), name='linkedin_login'),
    path('social/linkedin/connect/', social_views.LinkedinConnect.as_view(), name='linkedin_connect'),

    path('social/google/', social_views.GoogleLogin.as_view(), name='google_login'),
    path('social/google/connect/', social_views.GoogleConnect.as_view(), name='google_connect'),

    path('social/apple/', social_views.AppleLogin.as_view(), name='apple_login'),
    path('social/apple/connect/', social_views.AppleConnect.as_view(), name='apple_connect'),

    path('social/accounts/', social_views.SocialAccountListView.as_view(), name='social_account_list'),
    path('social/accounts/<int:pk>/disconnect/',
         social_views.SocialAccountDisconnectView.as_view(),
         name='social_account_disconnect'),

    path('network/', views.NetworkView.as_view(), name='network'),
    path('network/<pk>/', views.NetworkView.as_view(), name='other-profile'),
    path('referer/', views.RefererEmailView.as_view(), name='referer'),

    path('', include(router.urls)),
    path('public/', include(public_router.urls))

]

urlpatterns = [
    path('auth/', include(auth_urlpatterns))
]
