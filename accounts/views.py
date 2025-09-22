from typing import Any
from django.shortcuts import render
from django.contrib.auth import login
from django.db import transaction
from django.urls import reverse_lazy
from django.http import Http404
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, DetailView, UpdateView
from django_channels_chat import settings
from accounts.forms import UserCreationForm, UserLoginForm, ProfileUpdateForm, UserUpdateForm
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Авторизация"
        return context

    def get_success_url(self):
        return reverse_lazy("home")

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


def verify(request, uuid):
    try:
        user = User.objects.get(verification_uuid=uuid, is_verified=False)
    except User.DoesNotExist as e:
        raise Http404("User does not exist or is already verified") from e

    user.is_verified = True
    user.save()
    return render(request, "chat/home.html")


def email_verify(request):
    return render(request, "info/email_info.html")


class UserLogoutView(LogoutView):
    next_page = "user_login"


class ProfileUpdateView(UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = "accounts/profile_update.html"

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["user_form"] = UserUpdateForm(self.request.POST, instance=self.request.user)
        else:
            context["user_form"] = UserUpdateForm(instance=self.request.user)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context["user_form"]
        with transaction.atomic():
            if all([form.is_valid(), user_form.is_valid()]):
                user_form.save()
                form.save()
            else:
                return self.render_to_response(context)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy("profile_detail", kwargs={"slug": self.object.slug})
