from typing import Any
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, DetailView
from django_channels_chat import settings
from accounts.forms import UserCreationForm, UserLoginForm
from accounts.models import Profile
from chat.models import PrivateChat


User = get_user_model()


# Create your views here.
class UserRegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "accounts/user_register.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Регистрация"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        Profile.objects.create(user=user)
        login(self.request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
        return response


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "accounts/user_login.html"
    success_url = reverse_lazy("home")
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Авторизация"
        return context

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me", False)
        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        return super().form_valid(form)


class ProfileDetailView(DetailView):
    model = Profile
    template_name = "accounts/profile_detail.html"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        # pylint: disable=unused-variable
        context = super().get_context_data(**kwargs)
        profile = self.object
        current_user = self.request.user

        # Получаем или создаем приватный чат
        chat, created = PrivateChat.objects.get_or_create_chat(current_user, profile.user)

        context["title"] = f"Профиль: {profile.user.username}"
        context["private_chat_uuid"] = chat.uuid
        return context
