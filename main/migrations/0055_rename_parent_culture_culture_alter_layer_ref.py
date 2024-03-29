# Generated by Django 4.1.1 on 2023-01-06 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0054_remove_layer_related'),
    ]

    operations = [
        migrations.RenameField(
            model_name='culture',
            old_name='parent',
            new_name='culture',
        ),
        migrations.AlterField(
            model_name='layer',
            name='ref',
            field=models.ManyToManyField(blank=True, related_name='layer', to='main.reference', verbose_name='reference'),
        ),
    ]
