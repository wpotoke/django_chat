from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from accounts.models import Profile
from accounts.forms import UserCreationForm  # Рекомендую добавить форму изменения

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Формы
    add_form = UserCreationForm
    # form = UserChangeForm  Добавляем форму для редактирования

    # Отображение в списке
    list_display = ("username", "email", "phone_number", "is_active", "is_staff", "is_superuser", "created")
    list_filter = ("is_superuser", "is_staff", "is_active", "created")
    search_fields = ("username", "email", "phone_number")
    ordering = ("email",)
    readonly_fields = ("created",)  # Делаем дату создания только для чтения

    # Группировка полей при редактировании
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Контактная информация", {"fields": ("phone_number",)}),
        (
            "Права доступа",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        ("Важные даты", {"fields": ("last_login", "created")}),
    )

    # Поля при создании пользователя
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "phone_number", "password1", "password2"),
            },
        ),
    )

    # Фильтры по горизонтали (для групп и прав)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    # Дополнительные настройки
    list_per_page = 25  # Количество пользователей на странице
    list_max_show_all = 100  # Максимальное количество для "Show all"
    show_full_result_count = True  # Показывать полное количество


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "birthday", "slug")
    list_display_links = ("user", "slug")
