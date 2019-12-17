from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.forms import forms, ModelMultipleChoiceField, BooleanField, HiddenInput
from django.utils.translation import ugettext_lazy as _


class AdminCreationForm(UserCreationForm):

    groups = ModelMultipleChoiceField(queryset=Group.objects.filter(name__in=['Admin', 'Support']))
    is_staff = BooleanField(initial=True)

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
