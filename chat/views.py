from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from chat.models import Group, Message, Event


@login_required
def home_view(request):
    """Главная страница, на которой перечислены все группы"""
    groups = Group.objects.all()
    user = request.user
    context = {"groups": groups, "user": user}
    return render(request, template_name="chat/home.html", context=context)


@login_required
def group_chat_view(request, uuid):
    """Представление для группы, где все сообщения и события отправляются на интерфейс"""

    group = get_object_or_404(Group, uuid=uuid)
    if not group.members.filter(id=request.user.id).exists():
        return HttpResponseForbidden(
            "You are not a member of this group.\
                                       Kindly use the join button"
        )

    messages = group.message_set.all()
    events = group.event_set.all()
    # События - это сообщения, которые указывают
    # Что пользователь присоединился к группе или покинул ее.
    # Они будут отправлены автоматически, когда пользователь присоединится к группе или покинет ее.

    # Сортируем по метке времени так, чтобы они были перечислены по порядку
    message_and_event_list = [*messages, *events]
    sorted_message_event_list = sorted(message_and_event_list, key=lambda x: x.timestamp)

    group_members = group.members.all()

    context = {
        "message_and_event_list": sorted_message_event_list,
        "group_members": group_members,
    }

    return render(request, template_name="chat/groupchat.html", context=context)
