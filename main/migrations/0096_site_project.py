# Generated by Django 4.1 on 2023-09-17 19:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0095_project_namespace_project_password_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="project",
            field=models.ManyToManyField(
                blank=True, related_name="site", to="main.project"
            ),
        ),
    ]
