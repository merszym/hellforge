# Generated by Django 4.1 on 2024-06-13 09:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0133_date_sigma"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="visible",
            field=models.BooleanField(default=True, verbose_name="visible"),
        ),
    ]
