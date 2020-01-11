import json
from django.shortcuts import render
from django.utils.safestring import mark_safe


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
