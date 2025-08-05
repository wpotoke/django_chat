from django.urls import path
from chat import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("chats/", views.chat_list, name="chat_list"),
    path("groups/<uuid:uuid>/", views.group_chat_view, name="group"),
    # path("chats/<uuid:uuid>/", ) view not
]
