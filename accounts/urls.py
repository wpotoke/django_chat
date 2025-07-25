from django.urls import path
from accounts.views import UserRegisterView, index

urlpatterns = [path("home/", index, name="home"), path("register/", UserRegisterView.as_view(), name="user_register")]
