# Generated by Django 4.1.1 on 2023-01-05 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0052_layer_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='epoch',
            name='loc',
        ),
    ]
