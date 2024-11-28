# Generated by Django 5.1.3 on 2024-11-28 09:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0153_analyzedsample_efficiency_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='HumanDiagnosticPositions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(blank=True, max_length=100, null=True, verbose_name='Version')),
                ('data', models.JSONField(blank=True, null=True, verbose_name='data')),
                ('analyzedsample', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='matthias_analysis', to='main.analyzedsample', verbose_name='analyzedsample')),
            ],
            options={
                'ordering': ['analyzedsample__sample__site', 'analyzedsample__sample__layer', 'analyzedsample__sample', 'analyzedsample__seqrun', 'analyzedsample__probes'],
            },
        ),
    ]