from consumers.chat.models import Message


def unread_messages(request):
    """
    Check if unread support message exists
    """
    return {'unread_messages': Message.objects.filter(is_support=True, is_read=False, receiver__isnull=True).exists()}
