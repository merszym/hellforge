# Generated by Django 4.1.1 on 2022-11-27 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_site_site_done'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='related',
            field=models.ManyToManyField(blank=True, to='main.layer', verbose_name='related layers'),
        ),
    ]
