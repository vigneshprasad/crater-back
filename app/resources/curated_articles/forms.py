from django import forms
from django.utils.translation import ugettext_lazy as _

from resources.curated_articles.models import CuratedArticle
from utils.fields import CachedMaterialAdminFileWidget


class CuratedArticleForm(forms.ModelForm):
    picture = forms.ImageField(widget=CachedMaterialAdminFileWidget)

    class Meta:
        model = CuratedArticle
        fields = '__all__'
