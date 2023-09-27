# Generated by Django 4.1 on 2023-09-27 09:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0098_layer_set_lower_layer_set_upper"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sample",
            name="description",
        ),
        migrations.AddField(
            model_name="sample",
            name="batch",
            field=models.CharField(
                blank=True, max_length=400, null=True, verbose_name="sample batch"
            ),
        ),
        migrations.AddField(
            model_name="sample",
            name="mean_lower",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sample",
            name="mean_upper",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sample",
            name="provenience",
            field=models.JSONField(blank=True, null=True, verbose_name="provenience"),
        ),
        migrations.AddField(
            model_name="sample",
            name="set_lower",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sample",
            name="set_upper",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sample",
            name="type",
            field=models.CharField(
                blank=True, max_length=400, null=True, verbose_name="sample type"
            ),
        ),
        migrations.AddField(
            model_name="sample",
            name="year_of_collection",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="year of collection"
            ),
        ),
        migrations.AlterField(
            model_name="sample",
            name="name",
            field=models.CharField(
                blank=True, max_length=200, null=True, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="sample",
            name="ref",
            field=models.ManyToManyField(
                blank=True,
                related_name="sample",
                to="main.reference",
                verbose_name="reference",
            ),
        ),
    ]
