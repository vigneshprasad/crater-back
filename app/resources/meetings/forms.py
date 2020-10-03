from django import forms

from resources.meetings import models


class MeetingConfigForm(forms.ModelForm):

    class Meta:
        model = models.Config
        fields = '__all__'
