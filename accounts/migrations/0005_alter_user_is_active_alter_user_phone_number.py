# Generated by Django 5.0 on 2025-07-25 17:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_remove_user_is_admin_user_groups_user_is_staff_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone_number",
            field=models.CharField(
                blank=True,
                max_length=12,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered in the format: '+79999999999' or '89999999999'.",
                        regex="^((\\+7)|8)\\d{10}$",
                    )
                ],
            ),
        ),
    ]
