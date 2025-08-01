# Generated by Django 5.0 on 2025-07-25 14:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.CharField(
                blank=True,
                error_messages={"unique": "This username already bussy."},
                max_length=30,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        code="invalid_username",
                        message="Username may only contain lowercase English letters and underscores",
                        regex="^[a-z_]+$",
                    )
                ],
            ),
        ),
    ]
