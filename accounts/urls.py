from django.urls import path
from accounts.views import UserRegisterView, index, UserLoginView

urlpatterns = [
    path("home/", index, name="home"),
    path("register/", UserRegisterView.as_view(), name="user_register"),
    path("login/", UserLoginView.as_view(), name="user_login"),
]
