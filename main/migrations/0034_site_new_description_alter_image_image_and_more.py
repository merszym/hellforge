# Generated by Django 4.1.1 on 2022-11-18 23:47

from django.db import migrations, models
import django.db.models.deletion
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0033_alter_site_gallery'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='new_description',
            field=models.JSONField(blank=True, null=True, verbose_name='new_description'),
        ),
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(upload_to=main.models.get_image_path, verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='site',
            name='gallery',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='model', to='main.gallery', verbose_name='gallery'),
        ),
    ]
