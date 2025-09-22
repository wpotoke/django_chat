from typing import Any
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django_recaptcha.fields import ReCaptchaField
from accounts.models import Profile


User = get_user_model()


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="password",
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "Create Password"}),
        help_text="Password must be at least 8 characters",
    )
    password2 = forms.CharField(
        min_length=8,
        required=True,
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "Confirm Password"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone_number",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "input", "placeholder": "Enter your username"}),
            "email": forms.EmailInput(attrs={"class": "input", "placeholder": "Enter your Email"}),
            "phone_number": forms.TextInput(attrs={"class": "input", "placeholder": "Phone number"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use. Please use a different email.")
        return email

    def clean(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")

        return self.cleaned_data

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if phone:  # проверяем только если номер не пустой
            if User.objects.filter(phone_number=phone).exclude(id=self.instance.id).exists():
                raise forms.ValidationError("Этот номер телефона уже занят")
        return phone


class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "input", "placeholder": "Enter your Email"}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "Enter your Password"})
    )
    remember_me = forms.BooleanField(required=False, label="Remember me")
    recaptcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if not self.user_cache:
                raise forms.ValidationError("Invalid email or password")
        return cleaned_data

    def get_user(self):
        return self.user_cache


class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=30)
    phone_number = forms.CharField(max_length=12, required=False)

    class Meta:
        model = User
        fields = ["username", "phone_number"]


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=200)
    last_name = forms.CharField(max_length=255)
    avatar = forms.ImageField(required=False)
    bio = forms.CharField(max_length=192, required=False)
    birthday = forms.DateField(required=False)

    class Meta:
        model = Profile
        fields = ["first_name", "last_name", "avatar", "bio", "birthday"]
