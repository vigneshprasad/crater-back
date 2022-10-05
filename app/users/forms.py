import re

from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, UsernameField, AuthenticationForm, \
    SetPasswordForm, PasswordResetForm
from django.contrib.auth.models import Group
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from tags import models as tags_models
from users.models import Admin, Profile
from utils.fields import CachedMaterialAdminFileWidget


class AdminCreationForm(UserCreationForm):

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all())
    is_staff = forms.BooleanField(initial=True)

    class Meta:
        model = get_user_model()
        fields = ("name", "email", "is_staff", "groups", "is_superuser", "is_active")
        widgets = {
            "groups": forms.SelectMultiple(),
        }

    @staticmethod
    def clean_is_staff():
        return True


class UserForm(UserChangeForm):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)
    city = forms.ModelChoiceField(
        queryset=tags_models.CityProxy.objects.all(),
        required=False
    )
    objectives = forms.ModelMultipleChoiceField(
        queryset=tags_models.Objective.objects.all(),
        required=False
    )

    class Meta:
        model = get_user_model()
        fields = "__all__"
        field_classes = {"username": UsernameField}


class FreelanceAdminAuthenticationForm(AdminAuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(attrs={'autofocus': True}),
        error_messages={
            'required': _('Please enter your email.'),
        }
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
        error_messages={
            'required': _('Please enter the password.'),
        }
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': _(
            "Please enter the correct %(username)s and password for a staff "
            "account."
        ),
    }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError(_('Please enter your email'))
        if '@' not in username or len(username) > 100:
            raise ValidationError(_('Please enter a valid email'))
        return username.lower()


class AdminSetPasswordForm(SetPasswordForm):

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if len(password1) < 8:
            raise forms.ValidationError(_('Password should have 8 or more symbols'))
        if not re.search(r'\d', password1) or not re.search(r'\D', password1):
            raise forms.ValidationError(_('Password should contain numbers and letters'))
        return password1


class AdminPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        active_users = Admin._default_manager.filter(**{
            '%s__iexact' % Admin.get_email_field_name(): email,
            'is_active': True,
        })
        return (u for u in active_users if u.has_usable_password())


class ProfileForm(forms.ModelForm):

    photo = forms.ImageField(widget=CachedMaterialAdminFileWidget, required=False)
    primary_url = forms.URLField(required=False)

    class Meta:
        model = Profile
        fields = (
            "photo",
            "photo_url",
            "cover",
            "introduction",
            "linkedin_url",
            "instagram",
            "twitter",
            "primary_url",
            "allow_meeting_request",
            "opted_in_for_whatsapp",
            "new_tag",
            "education_level",
            "years_of_experience",
            "company_type",
            "stage_of_company",
            "company_name",
            "number_of_employees",
            "company_type_advised",
            "sector",
            "project_type",
            "companies_invested",
            "aspiration"
        )
