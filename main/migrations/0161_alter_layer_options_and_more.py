# Generated by Django 5.1.3 on 2025-04-09 10:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0160_alter_profilelayerjunction_layer_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='layer',
            options={},
        ),
        migrations.AlterModelOptions(
            name='profilelayerjunction',
            options={'ordering': ['position']},
        ),
        migrations.AlterModelOptions(
            name='sample',
            options={'ordering': ['site', 'batch', 'layer', 'name']},
        ),
        migrations.RemoveField(
            model_name='layer',
            name='pos',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='profile',
        ),
    ]
