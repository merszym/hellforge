# Generated by Django 4.1 on 2023-01-24 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0062_remove_layer_reldate_relativedate_layer'),
    ]

    operations = [
        migrations.AddField(
            model_name='date',
            name='raw',
            field=models.JSONField(blank=True, null=True, verbose_name='calibrationcurve_datapoints'),
        ),
    ]
