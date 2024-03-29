# Generated by Django 4.1.1 on 2022-10-21 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_layer_options_alter_profile_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkpoint',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='culture',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='date',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='epoch',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='layer',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='location',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='sample',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='site',
            name='description',
            field=models.TextField(blank=True, verbose_name='description'),
        ),
    ]
