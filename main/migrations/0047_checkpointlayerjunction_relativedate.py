# Generated by Django 4.1.1 on 2022-12-20 15:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0046_alter_reference_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckpointLayerJunction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Checkpoint', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='junction', to='main.checkpoint', verbose_name='checkpoint')),
                ('Layer', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='junction', to='main.layer', verbose_name='layer')),
            ],
        ),
        migrations.CreateModel(
            name='RelativeDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('how', models.CharField(choices=[('same', 'Same Age'), ('younger', 'Younger'), ('older', 'Older')], max_length=20, verbose_name='how')),
                ('offset', models.IntegerField(default=0, verbose_name='offset')),
                ('ref', models.ManyToManyField(blank=True, to='main.reference', verbose_name='reference')),
                ('relation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.checkpointlayerjunction', verbose_name='relation')),
            ],
        ),
    ]