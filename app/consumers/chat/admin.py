from django.contrib.admin import register, ModelAdmin
from django.db.models import Q
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import path
from django.core.exceptions import PermissionDenied
from django.templatetags.static import static as staticfiles
from rest_framework_jwt.utils import jwt_payload_handler, jwt_encode_handler

from consumers.chat.models import Chat, Message
from consumers.chat.tasks import read_admin_messages_for_user


@register(Chat)
class ChatAdmin(ModelAdmin):
    icon_name = 'chat'
    page_chat_template = 'chat/chat_page.html'

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path('', self.page_view, name='%s_%s_changelist' % info),
            path('<str:uuid>', self.page_detail_view, name='%s_%s_result' % info),
        ]

    def page_view(self, request):
        self._check_permissions(request)
        context = self._get_context(request)
        context['users'] = self._get_users(request)
        return TemplateResponse(request, self.page_chat_template, context)

    def page_detail_view(self, request, uuid):
        self._check_permissions(request)
        context = self._get_context(request)
        context['users'] = self._get_users(request, uuid)
        context['active_user'] = self._get_active_user(request, uuid)
        context['messages'] = Message.objects.filter(is_support=True).filter(Q(sender=uuid) | Q(receiver=uuid))
        context['uuid'] = uuid
        context['token'] = jwt_encode_handler(jwt_payload_handler(request.user))
        read_admin_messages_for_user.delay(uuid)
        return TemplateResponse(request, self.page_chat_template, context)

    def _check_permissions(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

    def _get_context(self, request):
        return dict(
            self.admin_site.each_context(request),
            title='Chat',
        )

    @classmethod
    def _get_users(cls, request, uuid=None):
        qs = Message.objects.filter(
                is_support=True, receiver__isnull=True
            ).exclude(sender_id=uuid).order_by('sender_id', '-created').distinct('sender')
        messages = [
            {
                'name': message.sender.name,
                'photo': cls._get_photo(request, message.sender),
                'pk': str(message.sender.pk),
                'unread': cls._get_unread_messages_count(message.sender),
                'message': cls._get_latest_message(message.sender),
            } for message in qs.exclude(sender_id=uuid)
        ]
        return [u for u in sorted(messages, key=lambda item: item['message'].created, reverse=True)]

    @staticmethod
    def _get_latest_message(user):
        return Message.objects.filter(Q(sender=user) | Q(receiver=user), is_support=True).last()

    @staticmethod
    def _get_unread_messages_count(user):
        return Message.objects.filter(sender=user, is_read=False, is_support=True).count()

    @classmethod
    def _get_active_user(cls, request, uuid):
        message = Message.objects.filter(sender_id=uuid).last()
        if not message:
            raise Http404()
        return {
            'name': message.sender.name,
            'photo': cls._get_photo(request, message.sender),
            'pk': str(message.sender.pk),
            'message': message.message,
        }

    @staticmethod
    def _get_photo(request, user):
        if hasattr(user, 'profile') and user.profile.photo:
            return request.build_absolute_uri(user.profile.photo.url)
        return staticfiles('admin/logo.jpg')
