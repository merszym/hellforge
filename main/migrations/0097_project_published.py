# Generated by Django 4.1 on 2023-09-22 16:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0096_site_project"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="published",
            field=models.BooleanField(default=False, verbose_name="published"),
        ),
    ]
