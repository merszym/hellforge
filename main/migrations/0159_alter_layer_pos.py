# Generated by Django 5.1.3 on 2025-04-09 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0158_remove_layer_characteristics_remove_layer_unit_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='pos',
            field=models.IntegerField(blank=True, null=True, verbose_name='position in profile'),
        ),
    ]
