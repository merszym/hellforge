# Generated by Django 5.1.3 on 2025-01-09 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0154_humandiagnosticpositions'),
    ]

    operations = [
        migrations.AddField(
            model_name='reference',
            name='bibtex',
            field=models.TextField(blank=True, verbose_name='bibtex'),
        ),
    ]
