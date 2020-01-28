import copy
import json
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView

from consumers.chat.models import Message


def index(request):
    return render(request, 'chat/index.html', {})


def chat(request, user_id, token):
    return render(request, 'chat/room.html', {
        'user_id': mark_safe(json.dumps(user_id)),
        'token': mark_safe(json.dumps(token)),
    })


def support(request, token):
    return render(request, 'chat/support.html', {
        'token': mark_safe(json.dumps(token)),
    })


def user_chat_page(request, token):
    return render(request, 'chat/user_chat_page.html', {
        'token': mark_safe(json.dumps(token)),
    })


class AdminChatFileView(CreateView):
    models = Message
    template_name = 'chat/chat_page.html'
    fields = ['sender', 'receiver', 'file', 'is_support']
    queryset = Message.objects.all()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        data = copy.copy(kwargs['data'])
        files = copy.copy(kwargs['files'])
        data.update({'is_support': True, 'sender': self.request.user.pk})
        return {
            'data': data,
            'files': files
        }

    def get_success_url(self):
        return reverse_lazy('admin:chat_chat_result', args=(self.object.receiver.pk,))
