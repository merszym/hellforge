# Generated by Django 4.1 on 2023-10-11 09:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0102_rename_parent_layer_layer"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="culture",
            name="description",
        ),
        migrations.AddField(
            model_name="culture",
            name="description_old",
            field=models.TextField(blank=True, verbose_name="description_old"),
        ),
    ]
