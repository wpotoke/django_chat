from typing import Any
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django_channels_chat import settings
from accounts.forms import UserCreationForm, UserLoginForm


User = get_user_model()


def index(request):
    return render(request, "base.html")


# Create your views here.
class UserRegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "accounts/user_register.html"
    success_url = reverse_lazy("user_login")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Регистрация"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
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
