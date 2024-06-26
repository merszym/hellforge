# Generated by Django 4.1 on 2024-03-28 15:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0125_alter_faunalassemblage_taxa"),
    ]

    operations = [
        migrations.CreateModel(
            name="FaunalAnalysis",
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
                    "method",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="Method"
                    ),
                ),
                (
                    "layer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="faunal_analysis",
                        to="main.layer",
                        verbose_name="layer",
                    ),
                ),
                (
                    "ref",
                    models.ForeignKey(
                        blank=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="main.reference",
                        verbose_name="reference",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FaunalResults",
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
                    "scientific_name",
                    models.CharField(
                        blank=True,
                        max_length=400,
                        null=True,
                        verbose_name="scientific name",
                    ),
                ),
                (
                    "order",
                    models.CharField(
                        blank=True, max_length=400, null=True, verbose_name="order"
                    ),
                ),
                (
                    "family",
                    models.CharField(
                        blank=True, max_length=400, null=True, verbose_name="family"
                    ),
                ),
                (
                    "taxid",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="TaxID"
                    ),
                ),
                (
                    "results",
                    models.JSONField(
                        blank=True, null=True, verbose_name="Faunal Results"
                    ),
                ),
                (
                    "analysis",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="faunal_results",
                        to="main.faunalanalysis",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="foundtaxon",
            name="taxon",
        ),
        migrations.RemoveField(
            model_name="taxon",
            name="analysis",
        ),
        migrations.DeleteModel(
            name="FaunalAssemblage",
        ),
        migrations.DeleteModel(
            name="FoundTaxon",
        ),
        migrations.DeleteModel(
            name="Taxon",
        ),
    ]
