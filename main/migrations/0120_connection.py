# Generated by Django 4.1 on 2024-01-29 11:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0119_person_orcid"),
    ]

    operations = [
        migrations.CreateModel(
            name="Connection",
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
                ("link", models.CharField(max_length=300, verbose_name="link")),
                (
                    "name",
                    models.CharField(
                        blank=True, max_length=500, null=True, verbose_name="name"
                    ),
                ),
                (
                    "short_description",
                    models.TextField(blank=True, verbose_name="short_description"),
                ),
            ],
        ),
    ]
