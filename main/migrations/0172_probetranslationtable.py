# Generated by Django 5.1.3 on 2025-07-23 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0171_alter_layer_options_sample_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProbeTranslationTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('probes', models.CharField(blank=True, max_length=200, null=True, verbose_name='probes')),
                ('content', models.CharField(blank=True, max_length=500, null=True, verbose_name='content')),
            ],
        ),
    ]
