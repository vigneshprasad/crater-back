from django import forms

from resources.meetings import models


class MeetingForm(forms.ModelForm):

    class Meta:
        model = models.Meeting
        fields = '__all__'
