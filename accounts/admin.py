from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .forms import UserCreationForm

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm

    list_display = ("username", "email", "phone_number", "is_admin")
    list_filter = ("is_admin",)
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Permissions", {"fields": ("is_admin",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "phone_number"),
            },
        ),
    )
    ordering = ("email",)
    filter_horizontal = ()
