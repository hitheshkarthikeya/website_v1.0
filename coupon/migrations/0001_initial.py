# Generated by Django 5.1.4 on 2025-01-01 11:58

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Coupon",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=50, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "discount_type",
                    models.CharField(
                        choices=[
                            ("percentage", "Percentage"),
                            ("fixed", "Fixed Amount"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "discount_value",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "min_amount",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
                ),
                (
                    "max_discount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                ("valid_from", models.DateTimeField(default=django.utils.timezone.now)),
                ("valid_to", models.DateTimeField()),
                ("usage_limit", models.IntegerField(default=1)),
                ("used_count", models.IntegerField(default=0)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        help_text="If set, only this user can use the coupon.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
