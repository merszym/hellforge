# Generated by Django 5.1.3 on 2025-02-03 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0156_description_exclude_from_print'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='colour',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='colour'),
        ),
        migrations.AddField(
            model_name='layer',
            name='colour_hex',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='colour_rgb'),
        ),
        migrations.AddField(
            model_name='layer',
            name='colour_munsell',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='colour_munsell'),
        ),
        migrations.AddField(
            model_name='layer',
            name='texture',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='texture'),
        ),
    ]
