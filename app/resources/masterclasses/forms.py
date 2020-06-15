from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import ugettext_lazy as _

from resources.masterclasses.models import MasterClass


class MasterClassForm(forms.ModelForm):
    cover = forms.FileField(
        label=_('Video'),
        # widget=CachedMaterialAdminFileWidget,
        validators=[FileExtensionValidator(allowed_extensions=['mov', 'mpeg', 'avi', 'mp4', '3gp', 'mwv', 'flv'])]
    )

    class Meta:
        model = MasterClass
        fields = '__all__'
