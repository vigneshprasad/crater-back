from django import forms
from django.utils.translation import ugettext_lazy as _

from resources.curated_articles.models import CuratedArticle
from utils.fields import CachedMaterialAdminFileWidget


class CuratedArticleForm(forms.ModelForm):
    picture = forms.ImageField(widget=CachedMaterialAdminFileWidget)
    website_link = forms.CharField()

    class Meta:
        model = CuratedArticle
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['website_link'] = forms.URLField(
            required=False,
            disabled=True,
            label=_('Website URL'),
            max_length=75,
            initial=self.instance.website_tag.url if self.instance.website_tag else None
        )
