# Generated by Django 4.1 on 2023-11-01 08:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0108_samplebatch_alter_sample_batch"),
    ]

    operations = [
        migrations.AddField(
            model_name="samplebatch",
            name="year_of_arrival",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="year_of_arrival"
            ),
        ),
    ]
