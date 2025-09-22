from django.urls import path
from accounts.views import (
    UserRegisterView,
    UserLoginView,
    ProfileDetailView,
    verify,
    email_verify,
    UserLogoutView,
    ProfileUpdateView,
)

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user_register"),
    path("login/", UserLoginView.as_view(), name="user_login"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile_update"),
    path("profile/<slug:slug>/", ProfileDetailView.as_view(), name="profile_detail"),
    path("verify/<uuid:uuid>/", verify, name="verify"),
    path("email/verify/", email_verify, name="email_verify"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
]
