# Generated by Django 4.1.1 on 2022-12-04 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0037_layer_related'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='site',
            name='site_done',
        ),
    ]
