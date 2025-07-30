from django.urls import path
from chat import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("groups/<uuid:uuid>/", views.group_chat_view, name="group"),
]
