# Generated by Django 4.1 on 2024-01-29 11:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0120_connection"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="connections",
            field=models.ManyToManyField(
                blank=True, related_name="site", to="main.connection"
            ),
        ),
    ]
