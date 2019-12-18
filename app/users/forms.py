from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, UsernameField
from django.contrib.auth.models import Group
from django import forms
from django.utils.translation import ugettext_lazy as _


class AdminCreationForm(UserCreationForm):

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.filter(name__in=['Admin', 'Support']))
    is_staff = forms.BooleanField(initial=True)

    class Meta:
        model = get_user_model()
        fields = ('name', 'email', 'is_staff', 'groups', 'is_superuser')

    @staticmethod
    def clean_is_staff():
        return True

    def clean_groups(self):
        groups = self.cleaned_data.get('groups')
        if groups.count() > 1:
            raise forms.ValidationError(
                _('Admin must be related to only one role.'),
                code='one_role',
            )
        return groups


class UserForm(UserChangeForm):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.filter(name__in=['User', 'Investor']))

    class Meta:
        model = get_user_model()
        fields = '__all__'
        field_classes = {'username': UsernameField}
