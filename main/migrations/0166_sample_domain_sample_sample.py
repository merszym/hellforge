# Generated by Django 5.1.3 on 2025-04-14 12:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0165_alter_affiliationpersonjunction_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='domain',
            field=models.CharField(default='mpi_eva', max_length=100, verbose_name='domain'),
        ),
        migrations.AddField(
            model_name='sample',
            name='sample',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='parent', to='main.sample', verbose_name='sample'),
        ),
    ]
