# Generated by Django 4.1.1 on 2023-01-06 11:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0053_remove_epoch_loc'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='layer',
            name='related',
        ),
    ]
