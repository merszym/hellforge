# Generated by Django 4.1 on 2023-03-06 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0063_date_raw'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='date',
            options={'default_manager_name': 'visible_objects', 'ordering': ['upper']},
        ),
        migrations.AlterField(
            model_name='site',
            name='ref',
            field=models.ManyToManyField(blank=True, related_name='site', to='main.reference', verbose_name='reference'),
        ),
    ]
