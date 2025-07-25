from typing import Any
from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from accounts.forms import UserCreationForm


User = get_user_model()


def index(request):
    return render(request, "base.html")


# Create your views here.
class UserRegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "accounts/user_register.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Регистрация на сайте"
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
