from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from chat.models import Group, Message, Event, PrivateChat
from accounts.models import Profile


@login_required
def home_view(request):
    return render(request, "chat/home.html")


@login_required
def chat_list(request):
    """Главная страница, на которой перечислены все группы"""
    groups = Group.objects.all()
    user_id = request.user.id
    private_chats = PrivateChat.objects.filter(participants__id=user_id).all()
    print(private_chats)

    user = request.user
    context = {"groups": groups, "chats": private_chats, "user": user}
    return render(request, template_name="chat/chat_list.html", context=context)


@login_required
def group_chat_view(request, uuid):
    """Представление для группы, где все сообщения и события отправляются на интерфейс"""

    group = get_object_or_404(Group, uuid=uuid)
    if not group.members.filter(id=request.user.id).exists():
        return HttpResponseForbidden(
            "You are not a member of this group.\
                                       Kindly use the join button"
        )

    messages = group.message_set.select_related("author__profile").all()
    events = group.event_set.all()

    # События - это сообщения, которые указывают
    # Что пользователь присоединился к группе или покинул ее.
    # Они будут отправлены автоматически, когда пользователь присоединится к группе или покинет ее.

    message_and_event_list = list(messages) + list(events)
    message_and_event_list.sort(key=lambda x: x.timestamp)

    group_members = group.members.all()
    profile_members = Profile.objects.filter(user__in=group_members)

    context = {
        "message_and_event_list": message_and_event_list,
        "group_members": group_members,
        "profile_members": profile_members,
    }

    return render(request, template_name="chat/groupchat.html", context=context)


@login_required
def private_chat_view(request, uuid):
    private_chat = get_object_or_404(PrivateChat, uuid=uuid)
    if not private_chat.participants.filter(id=request.user.id).exists():
        return HttpResponseForbidden("You are not have chat with this user.")
    messages = private_chat.message_set.select_related("author__profile").order_by("timestamp")
    chat_members = private_chat.participants.all()
    profile_members = Profile.objects.filter(user__in=chat_members)

    context = {
        "message_and_event_list": messages,
        "group_members": chat_members,
        "profile_members": profile_members,
    }

    return render(request, template_name="chat/groupchat.html", context=context)
