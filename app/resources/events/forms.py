from django import forms


from resources.events.models import Event
from utils.fields import CachedMaterialAdminFileWidget


class EventForm(forms.ModelForm):
    picture = forms.ImageField(widget=CachedMaterialAdminFileWidget)

    class Meta:
        model = Event
        fields = '__all__'
