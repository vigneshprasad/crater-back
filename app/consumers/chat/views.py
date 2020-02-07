import copy
import json

from django.core.exceptions import ValidationError
from django.db import DataError
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.safestring import mark_safe
from django.views.generic import CreateView
from rest_framework import mixins, status

from consumers.chat.models import Message
from consumers.chat.serializers import MessageSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet



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


class MessageViewSet(mixins.CreateModelMixin, GenericViewSet):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        try:
            receiver_id = request.data.get('receiver_id')
            if receiver_id:
                msg = Message.objects.create(
                    message=request.data.get('message', ''),
                    receiver_id=receiver_id,
                    sender=request.user,
                    file=request.data['file']
                )
            else:
                msg = Message.objects.create(
                    message=request.data('message', ''),
                    sender=request.user,
                    file=request.data['file'],
                    is_support=True
                )
        except (MultiValueDictKeyError, ValidationError, KeyError, DataError) as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
