# Generated by Django 4.1 on 2023-01-18 15:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0060_site_parent_alter_layer_reldate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='gallery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='image', to='main.gallery'),
        ),
        migrations.AlterField(
            model_name='relativedate',
            name='relation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reldate', to='main.checkpointlayerjunction', verbose_name='relation'),
        ),
    ]
