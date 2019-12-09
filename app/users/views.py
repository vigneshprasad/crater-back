from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    post_reset_login = True
    success_url = reverse_lazy('home')
