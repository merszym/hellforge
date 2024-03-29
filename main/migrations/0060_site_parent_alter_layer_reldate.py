# Generated by Django 4.1 on 2023-01-18 10:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0059_alter_date_options_alter_date_managers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child', to='main.site', verbose_name='parent'),
        ),
        migrations.AlterField(
            model_name='layer',
            name='reldate',
            field=models.ManyToManyField(blank=True, related_name='layer', to='main.relativedate', verbose_name='relative date'),
        ),
    ]
