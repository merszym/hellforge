# Generated by Django 4.1 on 2023-09-05 12:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0093_project_description_project"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="name",
            field=models.CharField(max_length=200, unique=True, verbose_name="name"),
        ),
    ]
