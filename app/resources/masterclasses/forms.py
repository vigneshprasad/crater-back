from django import forms
from django.core.validators import FileExtensionValidator

from resources.masterclasses.models import MasterClass
from utils.fields import CachedMaterialAdminFileWidget
from django.utils.translation import ugettext_lazy as _


class MasterClassForm(forms.ModelForm):
    cover = forms.FileField(
        label=_('Video'),
        widget=CachedMaterialAdminFileWidget,
        validators=[FileExtensionValidator(allowed_extensions=['mov', 'mpeg', 'avi', 'mp4', '3gp', 'mwv', 'flv'])]
    )

    class Meta:
        model = MasterClass
        fields = '__all__'
