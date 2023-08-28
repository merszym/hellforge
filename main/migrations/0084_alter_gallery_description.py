# Generated by Django 4.1 on 2023-08-23 14:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0083_remove_site_ref"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gallery",
            name="description",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="gallery",
                to="main.description",
                verbose_name="description",
            ),
        ),
    ]