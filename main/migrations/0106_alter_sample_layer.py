# Generated by Django 4.1 on 2023-10-31 00:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0105_site_coredb_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sample",
            name="layer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sample",
                to="main.layer",
                verbose_name="layer",
            ),
        ),
    ]
