from django.urls import path
from accounts.views import UserRegisterView, UserLoginView, ProfileDetailView

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user_register"),
    path("login/", UserLoginView.as_view(), name="user_login"),
    path("profile/<slug:slug>/", ProfileDetailView.as_view(), name="profile_detail"),
]
