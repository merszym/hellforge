# Generated by Django 4.1.1 on 2022-11-02 12:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0025_alter_culture_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='epoch',
            options={'ordering': ['date__upper']},
        ),
        migrations.RemoveField(
            model_name='checkpoint',
            name='mean_lower',
        ),
        migrations.RemoveField(
            model_name='checkpoint',
            name='mean_upper',
        ),
        migrations.RemoveField(
            model_name='epoch',
            name='mean_lower',
        ),
        migrations.RemoveField(
            model_name='epoch',
            name='mean_upper',
        ),
    ]
