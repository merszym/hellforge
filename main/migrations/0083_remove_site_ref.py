# Generated by Django 4.1 on 2023-08-23 13:56

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0082_alter_description_content_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="site",
            name="ref",
        ),
    ]
