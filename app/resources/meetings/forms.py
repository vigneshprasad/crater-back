from django import forms

from resources.meetings import models


class MeetingConfigForm(forms.ModelForm):

    class Meta:
        model = models.MeetingConfig
        fields = '__all__'
