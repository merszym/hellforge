# Generated by Django 4.1 on 2023-10-30 12:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0104_remove_culture_description_old"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="coredb_id",
            field=models.CharField(
                blank=True, max_length=4, null=True, verbose_name="coreDB Id"
            ),
        ),
    ]