# Generated by Django 4.1.1 on 2022-12-20 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0047_checkpointlayerjunction_relativedate'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='reldate',
            field=models.ManyToManyField(blank=True, to='main.relativedate', verbose_name='relative date'),
        ),
    ]
