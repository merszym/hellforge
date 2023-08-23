# Generated by Django 4.1 on 2023-08-23 12:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0077_gallery_description_alter_description_gallery"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="description",
            name="gallery",
        ),
        migrations.AlterField(
            model_name="gallery",
            name="description",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="gallery",
                to="main.description",
                verbose_name="description",
            ),
        ),
    ]
