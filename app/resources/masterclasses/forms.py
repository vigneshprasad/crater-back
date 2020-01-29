from django import forms
from django.core.validators import FileExtensionValidator

from resources.masterclasses.models import MasterClass
from utils.fields import CachedMaterialAdminFileWidget


class MasterClassForm(forms.ModelForm):
    cover = forms.FileField(
        widget=CachedMaterialAdminFileWidget,
        validators=[FileExtensionValidator(allowed_extensions=['mov', 'mpeg', 'avi', 'mp4', '3gp', 'mwv', 'flv'])]
    )

    class Meta:
        model = MasterClass
        fields = '__all__'
