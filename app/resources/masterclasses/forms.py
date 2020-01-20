from django import forms

from resources.masterclasses.models import MasterClass
from utils.fields import CachedMaterialAdminFileWidget


class MasterClassForm(forms.ModelForm):
    cover = forms.FileField(widget=CachedMaterialAdminFileWidget)

    class Meta:
        model = MasterClass
        fields = '__all__'
