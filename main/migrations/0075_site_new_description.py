# Generated by Django 4.1 on 2023-08-23 11:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0074_alter_contactperson_options_alter_foundtaxon_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="new_description",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="main.description",
            ),
        ),
    ]
