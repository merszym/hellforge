# Generated by Django 4.1 on 2023-10-05 15:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0100_sample_project"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sample",
            options={"ordering": ["name"]},
        ),
        migrations.RenameField(
            model_name="site",
            old_name="parent",
            new_name="site",
        ),
    ]