# Generated by Django 4.1 on 2024-07-03 08:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0141_quicksandanalysis"),
    ]

    operations = [
        migrations.AddField(
            model_name="analyzedsample",
            name="tags",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="tags"
            ),
        ),
    ]
