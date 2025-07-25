from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from accounts.manager import MyUserManager


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
    phone_number = models.CharField(validators=[phone_regex], max_length=12, null=True, blank=True, unique=True)
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
