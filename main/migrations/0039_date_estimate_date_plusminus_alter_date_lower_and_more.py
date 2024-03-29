# Generated by Django 4.1.1 on 2022-12-06 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0038_remove_site_site_done'),
    ]

    operations = [
        migrations.AddField(
            model_name='date',
            name='estimate',
            field=models.IntegerField(blank=True, null=True, verbose_name='estimate'),
        ),
        migrations.AddField(
            model_name='date',
            name='plusminus',
            field=models.IntegerField(blank=True, null=True, verbose_name='plusminus'),
        ),
        migrations.AlterField(
            model_name='date',
            name='lower',
            field=models.IntegerField(blank=True, null=True, verbose_name='lower bound'),
        ),
        migrations.AlterField(
            model_name='date',
            name='upper',
            field=models.IntegerField(blank=True, null=True, verbose_name='upper bound'),
        ),
    ]
