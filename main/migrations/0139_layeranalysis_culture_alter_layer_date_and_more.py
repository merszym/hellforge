# Generated by Django 4.1 on 2024-06-19 12:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0138_alter_layer_date_alter_layer_date_lower_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="layeranalysis",
            name="culture",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="layer_analysis",
                to="main.culture",
            ),
        ),
        migrations.AlterField(
            model_name="layer",
            name="date",
            field=models.ManyToManyField(
                blank=True,
                related_name="%(class)s_model",
                to="main.date",
                verbose_name="date",
            ),
        ),
        migrations.AlterField(
            model_name="layeranalysis",
            name="layer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="layer_analysis",
                to="main.layer",
                verbose_name="layer",
            ),
        ),
        migrations.AlterField(
            model_name="layeranalysis",
            name="site",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="layer_analysis",
                to="main.site",
            ),
        ),
        migrations.AlterField(
            model_name="sample",
            name="date",
            field=models.ManyToManyField(
                blank=True,
                related_name="%(class)s_model",
                to="main.date",
                verbose_name="date",
            ),
        ),
    ]
