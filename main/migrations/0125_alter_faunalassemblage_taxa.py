# Generated by Django 4.1 on 2024-03-28 14:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0124_alter_taxon_options_remove_taxon_common_name_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="faunalassemblage",
            name="taxa",
            field=models.ManyToManyField(
                related_name="faunalassemblage", to="main.foundtaxon"
            ),
        ),
    ]
