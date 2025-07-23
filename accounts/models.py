from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser


class User(AbstractBaseUser):
    email = models.EmailField(max_length=255, verbose_name="Email", unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    phone_regex = RegexValidator(
        regex=r"^((\+7)|8)\d{10}$",
        message="Phone number must be entered in the format: '+79999999999' or '89999999999'.",
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=12, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self):
        return str(self.email)

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin
