from django.contrib import messages
from django.contrib.admin import ModelAdmin, register, TabularInline
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from community.posts.models import Report, Post, File


class FileAdmin(TabularInline):
    model = File
    extra = 0
    fields = ('id', 'object', 'thumbnail', 'cover')
    readonly_fields = ('object', 'thumbnail', 'cover')

    def has_delete_permission(self, request, obj=None):
        return False

    def thumbnail(self, file):
        if file.file:
            return mark_safe('<a href="{}" target="_blank">{}</a>'.format(file.file.cover_thumbnail, _('Thumbnail')))

    def cover(self, file):
        if file.file:
            return mark_safe('<a href="{}" target="_blank">{}</a>'.format(file.file.cover_transcoder, _('Transcoder')))


@register(Post)
class PostAdmin(ModelAdmin):
    icon_name = 'short_text'
    list_display = ('message', 'group')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, post=None):
        return False

    inlines = [FileAdmin]


@register(Report)
class ReportAdmin(ModelAdmin):
    icon_name = 'warning'
    list_display = ('user', 'post_link', 'is_reviewed')
    list_editable = ('is_reviewed',)
    readonly_fields = ('user', 'post')

    actions = ['remove_selected_posts']

    def remove_selected_posts(self, request, queryset):
        posts = queryset.values_list('post', flat=True)
        Post.objects.filter(pk__in=posts).delete()
        queryset.delete()
        self.message_user(request, _('Remove posts with selected reports'), messages.SUCCESS)
    remove_selected_posts.short_description = _('Remove posts with selected reports')

    def post_link(self, report):
        post_admin_url = f'admin:{report.post._meta.app_label}_{report.post._meta.model_name}_change'
        return mark_safe('<a href="{}" target="_blank">{}</a>'.format(reverse(post_admin_url, args=(report.post.id,)), report.post))
    post_link.allow_tags = True
    post_link.short_description = _('Post')

    def has_add_permission(self, request):
        return False
