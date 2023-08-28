# Generated by Django 4.1 on 2023-05-02 11:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0064_alter_date_options_alter_site_ref"),
    ]

    operations = [
        migrations.CreateModel(
            name="FaunalAssemblage",
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
                    "layer",
                    models.ForeignKey(
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mammalian_assemblage",
                        to="main.layer",
                        verbose_name="layer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Taxon",
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
                    "common_name",
                    models.CharField(
                        blank=True,
                        max_length=400,
                        null=True,
                        verbose_name="common name",
                    ),
                ),
                (
                    "scientific_name",
                    models.CharField(
                        blank=True,
                        max_length=400,
                        null=True,
                        verbose_name="scientific name",
                    ),
                ),
                (
                    "family",
                    models.CharField(
                        blank=True, max_length=400, null=True, verbose_name="family"
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="MammalianAssemblage",
        ),
        migrations.AddField(
            model_name="faunalassemblage",
            name="mammals",
            field=models.ManyToManyField(to="main.taxon"),
        ),
        migrations.AddField(
            model_name="faunalassemblage",
            name="ref",
            field=models.ManyToManyField(
                blank=True, to="main.reference", verbose_name="reference"
            ),
        ),
    ]