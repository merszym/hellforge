# Generated by Django 4.1.1 on 2022-10-27 00:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_culture_parent_epoch_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='site',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='layer', to='main.site', verbose_name='site'),
        ),
    ]
