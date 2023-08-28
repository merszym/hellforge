# Generated by Django 4.1 on 2023-05-03 11:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0070_remove_faunalassemblage_layer_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="FoundTaxon",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "abundance",
                    models.CharField(max_length=300, verbose_name="abundance"),
                ),
                (
                    "taxon",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="found_taxa",
                        to="main.taxon",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="faunalassemblage",
            name="taxa",
            field=models.ManyToManyField(to="main.foundtaxon"),
        ),
    ]