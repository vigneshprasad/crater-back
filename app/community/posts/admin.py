from django.contrib import messages
from django.contrib.admin import ModelAdmin, register
from django.utils.translation import ugettext_lazy as _

from community.posts.models import Report, Post


@register(Report)
class ReportAdmin(ModelAdmin):
    icon_name = 'warning'
    list_display = ('user', 'post', 'is_reviewed')
    list_editable = ('is_reviewed',)

    actions = ['remove_selected_posts']

    def remove_selected_posts(self, request, queryset):
        posts = queryset.values_list('post', flat=True)
        Post.objects.filter(pk__in=posts).delete()
        queryset.delete()
        self.message_user(request, _('Remove posts with selected reports'), messages.SUCCESS)
    remove_selected_posts.short_description = _('Remove posts with selected reports')
