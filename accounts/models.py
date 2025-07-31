from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.urls import reverse
from accounts.manager import MyUserManager
from services.utils import unique_slugify


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z_]+$",
                message="Username may only contain lowercase English letters and underscores",
                code="invalid_username",
            )
        ],
        error_messages={
            "unique": "This username is already taken.",
        },
        verbose_name="Имя пользователя",
    )
    email = models.EmailField(max_length=255, verbose_name="Email", unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    phone_regex = RegexValidator(
        regex=r"^((\+7)|8)\d{10}$",
        message="Phone number must be entered in the format: '+79999999999' or '89999999999'.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=12, null=True, blank=True, unique=True, verbose_name="Номер телефона"
    )
    objects = MyUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return str(self.email)

    def has_perm(self, perm, obj=None) -> bool:
        return self.is_superuser or super().has_perm(perm, obj)

    def has_module_perms(self, app_label) -> bool:
        return self.is_superuser or super().has_module_perms(app_label)

    @property
    def is_admin(self) -> bool:
        return self.is_staff or self.is_superuser


class Profile(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="profile", verbose_name="Пользователь")
    slug = models.SlugField(max_length=255, blank=True, verbose_name="URL", unique=True)
    first_name = models.CharField(max_length=200, verbose_name="Имя", default="John")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия", default="Doe")
    avatar = models.ImageField(
        verbose_name="Аватар",
        upload_to="images/avatars/%Y/%m/%d",
        default="images/avatars/default.png",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=("png", "jpg", "jpeg"))],
    )
    bio = models.TextField(max_length=192, null=True, blank=True, verbose_name="Инфа о себе")
    birthday = models.DateField(null=True, blank=True, verbose_name="Дата рождения")

    class Meta:
        ordering = ("user",)
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.user.username, self.slug)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("profile_detail", kwargs={"slug": self.slug})
