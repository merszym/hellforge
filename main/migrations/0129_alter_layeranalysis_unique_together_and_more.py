# Generated by Django 4.1 on 2024-03-28 16:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0128_rename_faunalanalysis_layeranalysis"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="layeranalysis",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="layeranalysis",
            name="type",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="Type"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="layeranalysis",
            unique_together={("layer", "ref", "type")},
        ),
    ]
