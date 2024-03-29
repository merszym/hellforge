# Generated by Django 4.1 on 2023-08-23 12:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0075_site_new_description"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="description",
            name="author",
        ),
        migrations.CreateModel(
            name="Author",
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
                ("order", models.IntegerField(default=1, verbose_name="order")),
                (
                    "description",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="author",
                        to="main.description",
                        verbose_name="description",
                    ),
                ),
                (
                    "person",
                    models.ManyToManyField(
                        blank=True,
                        related_name="author",
                        to="main.contactperson",
                        verbose_name="peron",
                    ),
                ),
            ],
        ),
    ]
