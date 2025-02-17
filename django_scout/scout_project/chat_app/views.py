from django.shortcuts import render, get_object_or_404
from scout_app.models import ChatGroup
from django.contrib.auth.decorators import login_required

@login_required
def chat_view(request):
    chat_group = get_object_or_404(ChatGroup, group_name='public-chat')
    chat_messages = chat_group.chat_messages.all()
    return render(request, 'chat_app/chat.html',{'chat_messages': chat_messages})
