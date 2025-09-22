from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django_channels_chat.celery import app

User = get_user_model()


@app.task
def send_verification_email(user_id):
    try:
        user = User.objects.get(pk=user_id)

        context = {
            "verification_link": "http://127.0.0.1:8000"
            f"{reverse('verify', kwargs={'uuid': str(user.verification_uuid)})}",
            "username": user.username,
        }

        html_content = render_to_string("info/verify_email.html", context=context)

        send_mail(
            subject="Xam Chat: Verify your account",
            message=f"Follow this link to verify your acccount\n {context['verification_link']}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_content,
        )
    except User.DoesNotExist:
        print(f"Tried to send verification email to non-existing user {user_id}")
