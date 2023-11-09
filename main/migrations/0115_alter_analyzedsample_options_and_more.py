# Generated by Django 4.1 on 2023-11-09 15:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0114_alter_analyzedsample_project"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="analyzedsample",
            options={"ordering": ["sample__layer", "probes", "sample"]},
        ),
        migrations.AlterModelOptions(
            name="samplebatch",
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="samplebatch",
            name="gallery",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sample_batch",
                to="main.gallery",
            ),
        ),
        migrations.AlterField(
            model_name="analyzedsample",
            name="project",
            field=models.ManyToManyField(
                blank=True,
                related_name="analyzedsample",
                to="main.project",
                verbose_name="project",
            ),
        ),
    ]
