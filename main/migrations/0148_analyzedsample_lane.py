# Generated by Django 4.1 on 2024-08-29 12:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0147_project_ref"),
    ]

    operations = [
        migrations.AddField(
            model_name="analyzedsample",
            name="lane",
            field=models.CharField(default="lane1", max_length=50, verbose_name="lane"),
        ),
    ]
