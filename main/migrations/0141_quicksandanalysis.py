# Generated by Django 4.1 on 2024-06-23 19:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0140_alter_layer_mean_lower_alter_layer_mean_upper_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuicksandAnalysis",
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
                    "version",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="Version"
                    ),
                ),
                ("data", models.JSONField(blank=True, null=True, verbose_name="data")),
                (
                    "analyzedsample",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quicksand_analysis",
                        to="main.analyzedsample",
                        verbose_name="analyzedsample",
                    ),
                ),
            ],
        ),
    ]