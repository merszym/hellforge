# Generated by Django 4.1.1 on 2022-10-27 10:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_layer_site'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reference',
            name='pdf',
        ),
    ]
