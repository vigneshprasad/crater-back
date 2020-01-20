"""freelance URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.admin import AdminSite
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView, TemplateView
from django.contrib.auth import views as auth_views
from django.contrib import admin
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from allauth.socialaccount import views as socialaccount_views

from rest_framework import permissions

from users.auth_views import AdminPasswordResetView
from users.forms import FreelanceAdminAuthenticationForm
from users.views import PasswordResetConfirmView


AdminSite.login_form = FreelanceAdminAuthenticationForm


schema_view = get_schema_view(
   openapi.Info(
      title="Freelance API",
      default_version='v1',
      description="Freelance API documentation",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('chat/', include(('chat.urls', 'chat'), namespace='chat')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
] + i18n_patterns(
    path('admin/', admin.site.urls, name='admin'),
    path('admin/password_reset/', AdminPasswordResetView.as_view(), name='admin_password_reset'),
    path('admin/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('admin/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    path('v1/', include('freelance.routers.v1')),
    path('account-confirm-email/<key>/', TemplateView.as_view(), name='account_confirm_email'),
    path('account-signup/', socialaccount_views.signup, name='socialaccount_signup'),

    path('', RedirectView.as_view(url='admin/', permanent=False), name='home'),
    prefix_default_language=False
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)
