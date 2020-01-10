from django.contrib.auth.views import PasswordResetView

from users.forms import AdminPasswordResetForm


class AdminPasswordResetView(PasswordResetView):
    form_class = AdminPasswordResetForm
